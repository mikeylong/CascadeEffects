from __future__ import annotations

from typing import Any


REJECT_TAG_BACKFILL: dict[tuple[str, str, str], tuple[str, ...]] = {
    ("challenger", "visual_research", "visual_research"): ("missing_contact_sheet",),
    ("challenger", "packaging_still", "launch_thumbnail"): ("unrecognizable_anchor", "text_artifacts"),
    ("challenger", "packaging_still", "launch_shorts_cover"): ("unrecognizable_anchor",),
    ("challenger", "scene_still", "launch_commit_console"): ("duplicate_human_identity",),
    ("challenger", "scene_still", "routine_console_wide"): ("text_artifacts",),
    ("therac-25", "visual_research", "visual_research"): ("too_abstract",),
    ("therac-25", "packaging_still", "therac_thumbnail"): ("scanline_banding",),
    ("therac-25", "packaging_still", "therac_shorts_cover"): ("scanline_banding",),
    ("therac-25", "scene_still", "console_alarm_hero"): ("overscaled_ripped_paper",),
    ("therac-25", "motion_asset", "console_alarm_push"): ("motion_too_short",),
}

VISUAL_RESEARCH_OPTION_DEFAULTS = {
    "opening_candidate_min": 6,
    "opening_candidate_target": 8,
    "subject_candidate_min": 2,
    "act_candidate_min": 8,
}

EPISODE_GUARDRAIL_DEFAULTS: dict[str, dict[str, Any]] = {
    "challenger": {
        "signal_object": "Space Shuttle Challenger",
        "banned_motifs": [
            "heroic astronaut portraiture",
            "launch-poster triumph",
            "paper close-ups that depend on readable text",
            "courtroom shorthand",
            "explosion spectacle as the main emotional register",
            "duplicated or mirrored control-room faces",
        ],
    },
    "therac-25": {
        "signal_object": "Therac-25 treatment machine",
        "banned_motifs": [
            "printouts or maintenance paperwork",
            "gore or victim framing",
            "clean hospital-overview beauty shots",
            "readable interface glyphs",
        ],
    },
}


def normalize_string_list(value: Any) -> list[str]:
    if isinstance(value, (list, tuple)):
        seen: set[str] = set()
        result: list[str] = []
        for item in value:
            normalized = str(item).strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            result.append(normalized)
        return result
    return []


def normalize_review_tags(value: Any) -> list[str]:
    return normalize_string_list(value)


def infer_reject_tags(
    episode_id: str,
    gate_type: str,
    item_id: str,
    *,
    current_tags: Any = None,
) -> list[str]:
    normalized = normalize_review_tags(current_tags)
    if normalized:
        return normalized
    key = (str(episode_id).strip(), str(gate_type).strip(), str(item_id).strip())
    return list(REJECT_TAG_BACKFILL.get(key, ()))


def derive_latest_reject_tags(manifest: dict[str, Any]) -> list[str]:
    visual_research = manifest.get("visual_research", {})
    approval = visual_research.get("approval", {})
    collected: list[str] = []

    def add_tags(value: Any) -> None:
        for tag in normalize_review_tags(value):
            if tag not in collected:
                collected.append(tag)

    if str(approval.get("status", "")).strip() == "rejected":
        add_tags(approval.get("tags"))
    for item in manifest.get("scene_stills", {}).get("items", []):
        if str(item.get("review_status", "")).strip() == "rejected":
            add_tags(item.get("review_tags"))
        if str(item.get("motion_review_status", "")).strip() == "rejected":
            add_tags(item.get("motion_review_tags"))
    for item in manifest.get("packaging_stills", {}).get("items", []):
        if str(item.get("review_status", "")).strip() == "rejected":
            add_tags(item.get("review_tags"))
    for item in manifest.get("motion_assets", {}).get("items", []):
        if str(item.get("review_outcome", "")).strip() == "rejected":
            add_tags(item.get("review_tags"))
    return collected


def derive_visual_research_guardrails(
    episode_id: str,
    opening_sequence: dict[str, Any],
    acts: list[dict[str, Any]],
    raw_guardrails: Any,
    latest_reject_tags: Any,
    source_inventory_summary: Any = None,
) -> dict[str, Any]:
    guardrails = raw_guardrails if isinstance(raw_guardrails, dict) else {}
    defaults = EPISODE_GUARDRAIL_DEFAULTS.get(str(episode_id).strip(), {})
    source_summary = source_inventory_summary if isinstance(source_inventory_summary, dict) else {}
    signal_object = str(guardrails.get("signal_object", "")).strip()
    if not signal_object:
        signal_object = str(defaults.get("signal_object", "")).strip()
    if not signal_object:
        signal_object = str(opening_sequence.get("subject_object", "")).strip()
    banned_motifs = normalize_string_list(guardrails.get("banned_motifs"))
    if not banned_motifs:
        banned_motifs = normalize_string_list(defaults.get("banned_motifs"))
    opening_object_strategy = str(opening_sequence.get("object_strategy", "")).strip() or "episode_specific_cluster"
    opening_candidate_min = int(guardrails.get("opening_candidate_min", VISUAL_RESEARCH_OPTION_DEFAULTS["opening_candidate_min"]) or VISUAL_RESEARCH_OPTION_DEFAULTS["opening_candidate_min"])
    opening_candidate_target = int(guardrails.get("opening_candidate_target", VISUAL_RESEARCH_OPTION_DEFAULTS["opening_candidate_target"]) or VISUAL_RESEARCH_OPTION_DEFAULTS["opening_candidate_target"])
    subject_candidate_min = int(guardrails.get("subject_candidate_min", VISUAL_RESEARCH_OPTION_DEFAULTS["subject_candidate_min"]) or VISUAL_RESEARCH_OPTION_DEFAULTS["subject_candidate_min"])
    act_candidate_min = int(guardrails.get("act_candidate_min", VISUAL_RESEARCH_OPTION_DEFAULTS["act_candidate_min"]) or VISUAL_RESEARCH_OPTION_DEFAULTS["act_candidate_min"])
    opening_slots = [
        {
            "slot_id": str(slot.get("slot_id", "")).strip(),
            "display_label": str(slot.get("display_label", "")).strip(),
            "role": str(slot.get("role", "")).strip(),
            "object_scope": str(slot.get("object_scope", "")).strip(),
            "renderability": str(slot.get("renderability", "")).strip(),
            "visual_descriptor": str(slot.get("visual_descriptor", "")).strip(),
        }
        for slot in opening_sequence.get("slots", [])
        if isinstance(slot, dict) and str(slot.get("slot_id", "")).strip()
    ]
    generic_mass_market_slot_ids = [
        slot["slot_id"]
        for slot in opening_slots
        if slot["object_scope"] == "generic_mass_market"
    ]
    subject_opening_slot_id = next(
        (slot["slot_id"] for slot in opening_slots if slot["role"] == "subject_object"),
        "",
    )
    opening_candidate_total = int(source_summary.get("opening_candidate_total", 0) or 0)
    opening_subject_candidate_total = int(source_summary.get("opening_subject_candidate_total", 0) or 0)
    opening_supporting_candidate_total = int(source_summary.get("opening_supporting_candidate_total", 0) or 0)
    raw_opening_slot_candidate_totals = source_summary.get("opening_slot_candidate_totals", {})
    opening_slot_candidate_totals = raw_opening_slot_candidate_totals if isinstance(raw_opening_slot_candidate_totals, dict) else {}
    normalized_opening_slot_candidate_totals = {
        str(slot_id).strip(): int(total or 0)
        for slot_id, total in opening_slot_candidate_totals.items()
        if str(slot_id).strip()
    }
    raw_act_candidate_totals = source_summary.get("act_candidate_totals", {})
    act_candidate_totals = raw_act_candidate_totals if isinstance(raw_act_candidate_totals, dict) else {}
    normalized_act_candidate_totals = {
        str(act_id).strip(): int(total or 0)
        for act_id, total in act_candidate_totals.items()
        if str(act_id).strip()
    }
    underfilled_coverage_ids: list[str] = []
    if opening_candidate_total < opening_candidate_min:
        underfilled_coverage_ids.append("opening")
    if opening_subject_candidate_total < subject_candidate_min:
        underfilled_coverage_ids.append("opening_subject")
    missing_opening_slot_ids: list[str] = []
    for slot in opening_slots:
        slot_id = slot["slot_id"]
        slot_total = int(normalized_opening_slot_candidate_totals.get(slot_id, 0) or 0)
        if slot_total < 1:
            missing_opening_slot_ids.append(slot_id)
            underfilled_coverage_ids.append(f"opening_slot:{slot_id}")
        elif slot["role"] == "subject_object" and slot_total < subject_candidate_min:
            underfilled_coverage_ids.append(f"opening_slot:{slot_id}")
    for act in acts:
        act_id = str(act.get("id", "")).strip()
        if not act_id:
            continue
        if int(normalized_act_candidate_totals.get(act_id, 0) or 0) < act_candidate_min:
            underfilled_coverage_ids.append(act_id)
    normalized_latest_reject_tags = normalize_review_tags(latest_reject_tags)
    if source_summary.get("unresolved_source_ids") and "source_text_unresolved" not in normalized_latest_reject_tags:
        normalized_latest_reject_tags.append("source_text_unresolved")
    if underfilled_coverage_ids and "insufficient_option_range" not in normalized_latest_reject_tags:
        normalized_latest_reject_tags.append("insufficient_option_range")
    return {
        "signal_object": signal_object,
        "banned_motifs": banned_motifs,
        "opening_object_strategy": opening_object_strategy,
        "latest_reject_tags": normalized_latest_reject_tags,
        "opening_candidate_min": opening_candidate_min,
        "opening_candidate_target": opening_candidate_target,
        "subject_candidate_min": subject_candidate_min,
        "act_candidate_min": act_candidate_min,
        "source_total": int(source_summary.get("source_total", 0) or 0),
        "approved_source_total": int(source_summary.get("approved_source_total", 0) or 0),
        "clear_source_total": int(source_summary.get("clear_source_total", 0) or 0),
        "cleaned_source_total": int(source_summary.get("cleaned_source_total", 0) or 0),
        "ready_source_total": int(source_summary.get("ready_source_total", 0) or 0),
        "opening_candidate_total": opening_candidate_total,
        "opening_subject_candidate_total": opening_subject_candidate_total,
        "opening_supporting_candidate_total": opening_supporting_candidate_total,
        "opening_subject_slot_id": subject_opening_slot_id,
        "generic_mass_market_slot_ids": generic_mass_market_slot_ids,
        "opening_slot_candidate_totals": normalized_opening_slot_candidate_totals,
        "missing_opening_slot_ids": missing_opening_slot_ids,
        "act_candidate_totals": normalized_act_candidate_totals,
        "underfilled_coverage_ids": underfilled_coverage_ids,
        "ready_for_generation": bool(source_summary.get("ready_for_generation", False)),
        "unresolved_source_ids": normalize_string_list(source_summary.get("unresolved_source_ids")),
        "blocked_source_ids": normalize_string_list(source_summary.get("blocked_source_ids")),
        "missing_downstream_source_ids": normalize_string_list(source_summary.get("missing_downstream_source_ids")),
    }


__all__ = [
    "EPISODE_GUARDRAIL_DEFAULTS",
    "REJECT_TAG_BACKFILL",
    "VISUAL_RESEARCH_OPTION_DEFAULTS",
    "derive_latest_reject_tags",
    "derive_visual_research_guardrails",
    "infer_reject_tags",
    "normalize_review_tags",
    "normalize_string_list",
]
