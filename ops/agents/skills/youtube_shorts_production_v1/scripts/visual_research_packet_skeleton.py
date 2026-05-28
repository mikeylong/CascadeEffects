#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path
from typing import Any


STYLE_SKILL_PATH = "/Users/mike/CascadeEffects/archive/season-01-reference/legacy-style-packages/style-packages/source_preserving_documentary_v1/SKILL.md"
SUBJECT_RENDER_MATRIX_PATH = (
    "/Users/mike/CascadeEffects/archive/season-01-reference/legacy-style-packages/style-packages/source_preserving_documentary_v1/"
    "judgment/subject_render_matrix.md"
)
HEADING_RE = re.compile(r"^(?P<level>#{3,4})\s+`?(?P<beat_id>[^`\n]+)`?\s*$")
FIELD_RE = re.compile(r"^\s*-\s*`(?P<key>[^`]+)`:\s*(?P<value>.*)$")
TIMED_LINE_RE = re.compile(
    "^\\[(?P<start>[0-9:.]+)\\s*(?:-|\\u2013|\\u2014)\\s*(?P<end>[0-9:.]+)\\]\\s*"
    "(?:(?:SPEAKER_\\d+|[A-Z][A-Z0-9 _.-]{1,32}):\\s*)?(?P<text>.*)$"
)


class PacketError(Exception):
    pass


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_value(raw: str) -> str:
    text = " ".join(str(raw or "").strip().split())
    if text.startswith("`") and text.endswith("`") and len(text) >= 2:
        text = text[1:-1]
    return text.strip()


def parse_timestamp(raw: str) -> float:
    parts = str(raw).strip().replace(",", ".").split(":")
    if len(parts) == 3:
        hours, minutes, seconds = parts
    elif len(parts) == 2:
        hours = "0"
        minutes, seconds = parts
    else:
        raise PacketError(f"Invalid timestamp: {raw!r}")
    return int(hours) * 3600.0 + int(minutes) * 60.0 + float(seconds)


def parse_cue_range(raw: str) -> tuple[float, float] | None:
    text = str(raw or "").strip().strip("`")
    if not text:
        return None
    normalized = re.sub("\\s*(?:-|\\u2013|\\u2014)\\s*", "-", text, count=1)
    if "-" not in normalized:
        return None
    start_raw, end_raw = normalized.split("-", 1)
    try:
        return parse_timestamp(start_raw), parse_timestamp(end_raw)
    except (PacketError, ValueError):
        return None


def normalize_transcript_text(raw: str) -> str:
    text = re.sub(r"<[^>]+>", " ", raw)
    text = re.sub(r"\[[^\]]+\]", " ", text)
    text = re.sub(r"^(?:SPEAKER_\d+|[A-Z][A-Z0-9 _.-]{1,32}):\s+", "", text.strip())
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_timed_transcript(text: str) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    for line in text.splitlines():
        match = TIMED_LINE_RE.match(line.strip())
        if not match:
            continue
        segment_text = normalize_transcript_text(match.group("text"))
        if not segment_text:
            continue
        segments.append(
            {
                "start": parse_timestamp(match.group("start")),
                "end": parse_timestamp(match.group("end")),
                "text": segment_text,
            }
        )
    return segments


def transcript_paragraphs(text: str) -> list[str]:
    paragraphs: list[str] = []
    for chunk in re.split(r"\n\s*\n", text.strip()):
        normalized = normalize_transcript_text(chunk)
        if normalized:
            paragraphs.append(normalized)
    return paragraphs


def parse_beat_plan(text: str) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    stack: dict[int, dict[str, Any]] = {}
    current: dict[str, Any] | None = None
    for line in text.splitlines():
        heading = HEADING_RE.match(line)
        if heading:
            level = len(heading.group("level"))
            beat_id = clean_value(heading.group("beat_id"))
            parent_id = stack[3]["id"] if level > 3 and 3 in stack else None
            node: dict[str, Any] = {
                "id": beat_id,
                "level": level,
                "parent_id": parent_id,
                "fields": {},
                "children": [],
            }
            if parent_id:
                stack[3]["children"].append(beat_id)
            stack[level] = node
            for existing_level in list(stack):
                if existing_level > level:
                    del stack[existing_level]
            nodes.append(node)
            current = node
            continue
        field = FIELD_RE.match(line)
        if field and current is not None:
            current["fields"][clean_value(field.group("key"))] = clean_value(field.group("value"))
    return nodes


def leaf_beats(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    leaves: list[dict[str, Any]] = []
    for node in nodes:
        fields = node["fields"]
        if node["children"]:
            continue
        if fields.get("cue_range") or fields.get("target_duration_seconds") or fields.get("primary_subject"):
            leaves.append(node)
    if not leaves:
        raise PacketError("Beat plan did not contain any leaf beats with cue_range or primary_subject fields.")
    return leaves


def transcript_excerpt_for_beat(
    beat: dict[str, Any],
    *,
    top_level_order: list[str],
    timed_segments: list[dict[str, Any]],
    paragraphs: list[str],
) -> str:
    fields = beat["fields"]
    cue = parse_cue_range(fields.get("cue_range", ""))
    if cue is not None and timed_segments:
        start, end = cue
        parts = [
            str(segment["text"])
            for segment in timed_segments
            if float(segment["end"]) >= start and float(segment["start"]) <= end
        ]
        if parts:
            return f"[{fields.get('cue_range')}] " + " ".join(parts)
    parent_id = str(beat.get("parent_id") or beat["id"])
    try:
        index = top_level_order.index(parent_id)
    except ValueError:
        index = 0
    if 0 <= index < len(paragraphs):
        return paragraphs[index]
    return "TODO: add narration excerpt for this beat from the approved caption transcript."


def packet_lines(
    *,
    episode_id: str,
    short_id: str,
    narration_map_path: Path,
    caption_source_path: Path,
    short_script_path: str,
    workflow_scope_manifest_path: str,
    dp_research_brief_path: str,
    archival_footage_review_path: str,
    dp_shot_packet_path: str,
    episode_constraint_ledger_path: str,
    exact_dp_imports: list[str],
    audio_package_sha256: str,
    transcript_sha256: str,
    nodes: list[dict[str, Any]],
    transcript_text: str,
) -> list[str]:
    timed_segments = parse_timed_transcript(transcript_text)
    paragraphs = transcript_paragraphs(transcript_text)
    top_level_order = [node["id"] for node in nodes if node["level"] == 3]
    lines = [
        f"# Visual Research Packet - {short_id}",
        "",
        "## Packet",
        "",
        f"- `episode_id`: `{episode_id}`",
        f"- `short_id`: `{short_id}`",
        f"- `workflow_scope_manifest_path`: `{workflow_scope_manifest_path or 'TODO: required before visual research'}`",
        f"- `dp_research_brief_path`: `{dp_research_brief_path or 'TODO: required before visual research'}`",
        f"- `narration_map_path`: `{narration_map_path}`",
        f"- `archival_footage_review_path`: `{archival_footage_review_path or 'pending unless archival motion is in scope'}`",
        "- `visual_beatmap_path`: `pending until DP derives after visual research`",
        f"- `dp_shot_packet_path`: `{dp_shot_packet_path or 'pending until visual beatmap is approved'}`",
        f"- `episode_constraint_ledger_path`: `{episode_constraint_ledger_path or 'pending until DP approval'}`",
        f"- `short_script_path`: `{short_script_path}`",
        "- `visual_spine_target`: `9 beats + short pre-beat`",
        "- `artifact_selection_thesis`: `engaging and visually stimulating`",
        "- `cue_ranges_path`: `same as narration_map_path`",
        f"- `caption_source_path`: `{caption_source_path}`",
        f"- `audio_package_sha256`: `{audio_package_sha256}`",
        f"- `transcript_sha256`: `{transcript_sha256}`",
        f"- `style_skill_path`: `{STYLE_SKILL_PATH}`",
        f"- `subject_render_matrix_path`: `{SUBJECT_RENDER_MATRIX_PATH}`",
        f"- `exact_dp_imports_used`: `{'; '.join(exact_dp_imports) if exact_dp_imports else 'none'}`",
        "- `disposition`: `tighten`",
        "- `blockers`: `Generated skeleton; fill evidence, complete the source-anchor map, request DP ledger approval, and keep may_enter_stills_contact_sheet false until ledger is active.`",
        "",
        "## Scope Compliance",
        "",
        "- `active_episode_short_root`: `TODO: from workflow scope manifest`",
        "- `active_episode_production_root`: `TODO: from workflow scope manifest`",
        "- `active_viz_short_root`: `TODO: from workflow scope manifest`",
        "- `used_only_scoped_paths`: `false`",
        "- `unapproved_legacy_paths_found`: `TODO`",
        "- `dp_import_requests`: `TODO`",
        "",
        "## Research Rules",
        "",
        "- Use references as constraints for subject identity, mechanism clarity, materials, setting, camera logic, and palette.",
        "- Do not copy a reference image, artist style, logo, readable archival text, UI, poster, or caption design into generated stills.",
        "- Keep research mechanism-led; a mood note alone is not enough to authorize still generation.",
        "- Apply the `engaging and visually stimulating` thesis during artifact selection itself because research artifacts drive downstream still and motion choices.",
        "- When archival motion is in scope, complete the archival footage review before the visual beatmap is locked.",
        "- Prefer scene-led research artifacts first, mechanism inserts second, and low-energy admin-detail props only as explicit exceptions.",
        "- Keep archival source breadth narrow: `1-3` primary videos plus at most `2` backups.",
        "- Under `strict clean`, any visible logo, stinger, lower-third, watermark, burned caption, end card, split screen, or channel bug is an automatic reject.",
        "- Every beat or shot must map to a recognizable source anchor or record a DP-approved `nonliteral_exception_approved`.",
        "- Approved sourced carriers are allowed when they are explicitly recorded as `carrier_mode: sourced` or `hybrid` with provenance.",
        "- If `coverage_class` is `object_cluster`, the selected carrier must remain a multi-object tableau with at least two approved artifacts visible in-frame.",
        "- One strong archival footage family may satisfy multiple narration lines; do not force one literal visual per script clause.",
        "- Do not inherit constraints from old Challenger/Hyatt/Therac/737 artifacts, old manifests, old renders, model experiments, keeper registries, casebooks, or packaging rules.",
        "- Treat all proposed constraints as inactive until the DP places them in the active episode constraint ledger.",
        "- Do not read `/archive/`, `/archives/`, `/experiments/`, `/legacy/`, `/retired/`, `/midjourney/`, `/proof_stills/`, diagnostic outputs, mixed-review outputs, old renders, or old manifests unless the workflow scope manifest lists the exact DP-approved import.",
        "- Name missing evidence as a deferred gap instead of inventing visual certainty.",
        "",
        "## Beat-Zone Research",
        "",
    ]
    for beat in leaf_beats(nodes):
        fields = beat["fields"]
        beat_id = beat["id"]
        primary_subject = fields.get("primary_subject", "TODO: define renderable primary subject")
        anomaly_carrier = fields.get("anomaly_carrier", "TODO: define one anomaly carrier")
        if anomaly_carrier.lower() in {"none", "none in the segment itself"}:
            allowed = "none; continuity/context beat unless coordinator reopens a visual contradiction"
        else:
            allowed = f"TODO: choose carriers from subject_render_matrix that can express: {anomaly_carrier}"
        lines.extend(
            [
                f"### `{beat_id}`",
                "",
                f"- `source_narration_range`: `{fields.get('cue_range', 'TODO')}`",
                f"- `narration_excerpt_or_transcript_range`: `{transcript_excerpt_for_beat(beat, top_level_order=top_level_order, timed_segments=timed_segments, paragraphs=paragraphs)}`",
                f"- `mechanism_claim`: `TODO: state the causal mechanism this beat must make visible.`",
                f"- `primary_subject`: `{primary_subject}`",
                "- `candidate_artifact_total`: `0`",
                "- `composition_mode`: `single_subject`",
                "- `lead_artifact_id`: `TODO`",
                "- `supporting_artifact_ids`: `TODO or none`",
                "- `optional_accent_artifact_ids`: `TODO or none`",
                "- `preferred_artifact_ids`: `TODO`",
                "- `backup_artifact_ids`: `TODO`",
                "- `preferred_clip_ids`: `TODO or none if archival motion is not in scope for this beat`",
                "- `backup_clip_ids`: `TODO or none if archival motion is not in scope for this beat`",
                "- `footage_family_id`: `TODO or not_in_scope`",
                "- `archive_reference_mode`: `reference_only`",
                "- `texture_influence`: `none`",
                f"- `canonical_subject_constraints`: `TODO: define what must remain recognizable about {primary_subject}.`",
                "- `source_anchor_id`: `TODO`",
                f"- `recognizable_source_anchor`: `TODO: name the concrete research artifact or scene family that must remain recognizable for {primary_subject}.`",
                "- `source_anchor_paths_or_urls`: `TODO`",
                "- `anchor_preservation_rule`: `TODO: state what identity must survive abstraction.`",
                "- `carrier_mode`: `generated`",
                "- `anchor_drift_fail_conditions`: `TODO: describe what would turn this beat into anonymous evidence-room drift.`",
                "- `nonliteral_exception_approved`: `false`",
                "- `coverage_class`: `TODO`",
                "- `object_cluster_rule`: `TODO if coverage_class is object_cluster; otherwise none`",
                "- `engagement_goal`: `TODO: state why this beat should feel engaging and visually stimulating.`",
                "- `mechanism_visibility_rule`: `TODO: state the one thing the frame must make legible.`",
                "- `coverage_exception_approved`: `false`",
                "- `constraint_hypotheses_from_research`: `TODO: proposed only; inactive until DP ledger approval.`",
                "- `historical_or_domain_reference_notes`: `TODO: add source-backed notes, not mood words.`",
                "- `reference_source_paths_or_urls`: `TODO`",
                "- `reference_source_quality`: `TODO`",
                "- `known_physical_scale_or_dimensions`: `TODO`",
                "- `literal_vs_representational_use`: `TODO`",
                "- `scene_custody_or_access_logic`: `TODO`",
                "- `scale_source_paths_or_urls`: `TODO`",
                "- `physical_plausibility_check`: `tighten`",
                "- `scale_or_custody_blockers`: `TODO`",
                "- `palette_material_constraints`: `TODO`",
                f"- `camera_logic`: `{fields.get('camera_logic', 'TODO: choose the camera logic that exposes this mechanism without hiding the subject.')}`",
                f"- `allowed_anomaly_carriers`: `{fields.get('allowed_anomaly_carriers', allowed)}`",
                "- `banned_anomaly_carriers`: `readable text, logos, UI overlays, poster graphics, extra surreal events, anatomy or geometry corruption`",
                "- `text_logo_ui_risks`: `TODO: identify likely text/logo/UI leakage risks before rendering.`",
                "- `deformation_or_model_risks`: `TODO: identify likely anatomy, geometry, vehicle, room, or document risks.`",
                f"- `still_prompt_hypothesis`: `{fields.get('still_strategy', 'TODO: write one concrete still prompt hypothesis from the research.')}`",
                f"- `motion_risk_note`: `{fields.get('motion_strategy', 'TODO: note motion risks before motion generation.')}`",
                "- `open_visual_questions`: `TODO`",
                "- `recommended_ledger_entries`: `TODO`",
                "- `research_disposition`: `tighten`",
                "",
                "#### Candidate Artifacts",
                "",
                "| artifact_id | artifact_priority_rank | artifact_engagement_score | mechanism_visibility_score | motion_potential_score | downstream_coverage_role | scene_family | artifact_selection_rationale |",
                "| --- | --- | --- | --- | --- | --- | --- | --- |",
                "| TODO | `1` | `1-5` | `1-5` | `1-5` | TODO | TODO | TODO |",
                "",
                "#### Candidate Clips",
                "",
                "| clip_id | timecode_in | timecode_out | source_family | clip_role | hygiene_status | selected_for_visual_beat | clip_selection_rationale |",
                "| --- | --- | --- | --- | --- | --- | --- | --- |",
                "| TODO | TODO | TODO | TODO | `reference_only` | `reject` | `false` | Fill from archival_footage_review when archival motion is in scope. |",
                "",
            ]
        )
    lines.extend(
        [
            "## Constraint Proposal Summary",
            "",
            "These proposals are not active until the DP approves them in the episode constraint ledger.",
            "",
            "| proposal_id | beat_or_shot_id | proposed_constraint | evidence_paths_or_urls | recommended_status | reason |",
            "| --- | --- | --- | --- | --- | --- |",
            "| TODO | TODO | TODO | TODO | `legacy_reference` | Generated skeleton; DP review required. |",
            "",
            "## Handoff",
            "",
            "- `may_enter_stills_contact_sheet`: `false`",
            "- `may_request_DP_ledger_approval`: `false`",
            "- `source_anchor_map_complete`: `false`",
            "- `artifact_rankings_complete`: `false`",
            "- `selected_research_gaps`: `Fill TODO fields and review packet before still generation.`",
            "- `next_action`: `Visual Research Agent fills evidence; DP approves active ledger before still generation.`",
            "",
        ]
    )
    return lines


def generate_packet(
    *,
    episode_id: str,
    short_id: str,
    narration_map_path: Path,
    caption_source_path: Path,
    short_script_path: str = "",
    workflow_scope_manifest_path: str = "",
    dp_research_brief_path: str = "",
    archival_footage_review_path: str = "",
    dp_shot_packet_path: str = "",
    episode_constraint_ledger_path: str = "",
    exact_dp_imports: list[str] | None = None,
    audio_package_sha256: str = "",
    transcript_sha256: str = "",
) -> str:
    if not narration_map_path.exists():
        raise PacketError(f"Narration map was not found: {narration_map_path}")
    if not caption_source_path.exists():
        raise PacketError(f"Caption source was not found: {caption_source_path}")
    transcript_hash = transcript_sha256 or file_sha256(caption_source_path)
    lines = packet_lines(
        episode_id=episode_id,
        short_id=short_id,
        narration_map_path=narration_map_path.resolve(),
        caption_source_path=caption_source_path.resolve(),
        short_script_path=short_script_path,
        workflow_scope_manifest_path=workflow_scope_manifest_path,
        dp_research_brief_path=dp_research_brief_path,
        archival_footage_review_path=archival_footage_review_path,
        dp_shot_packet_path=dp_shot_packet_path,
        episode_constraint_ledger_path=episode_constraint_ledger_path,
        exact_dp_imports=exact_dp_imports or [],
        audio_package_sha256=audio_package_sha256 or "TODO",
        transcript_sha256=transcript_hash,
        nodes=parse_beat_plan(narration_map_path.read_text(encoding="utf-8")),
        transcript_text=caption_source_path.read_text(encoding="utf-8-sig"),
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a YouTube Shorts visual research packet skeleton.")
    parser.add_argument("--episode-id", required=True)
    parser.add_argument("--short-id", required=True)
    parser.add_argument("--narration-map", required=True, type=Path)
    parser.add_argument("--caption-source", required=True, type=Path)
    parser.add_argument("--short-script", default="")
    parser.add_argument("--workflow-scope-manifest", default="")
    parser.add_argument("--dp-research-brief", default="")
    parser.add_argument("--archival-footage-review", default="")
    parser.add_argument("--dp-shot-packet", default="")
    parser.add_argument("--episode-constraint-ledger", default="")
    parser.add_argument("--exact-dp-import", action="append", default=[])
    parser.add_argument("--audio-package-sha256", default="")
    parser.add_argument("--transcript-sha256", default="")
    parser.add_argument("--output", type=Path, help="Optional output path. Defaults to stdout.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        text = generate_packet(
            episode_id=args.episode_id,
            short_id=args.short_id,
            narration_map_path=args.narration_map.expanduser().resolve(),
            caption_source_path=args.caption_source.expanduser().resolve(),
            short_script_path=args.short_script,
            workflow_scope_manifest_path=args.workflow_scope_manifest,
            dp_research_brief_path=args.dp_research_brief,
            archival_footage_review_path=args.archival_footage_review,
            dp_shot_packet_path=args.dp_shot_packet,
            episode_constraint_ledger_path=args.episode_constraint_ledger,
            exact_dp_imports=args.exact_dp_import,
            audio_package_sha256=args.audio_package_sha256,
            transcript_sha256=args.transcript_sha256,
        )
    except PacketError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    if args.output:
        output = args.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
        print(f"INFO visual research packet skeleton -> {output}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
