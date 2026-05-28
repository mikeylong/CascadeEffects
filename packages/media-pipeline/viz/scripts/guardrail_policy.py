from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_guardrail_policy(repo_root: Path) -> dict[str, Any]:
    path = Path(repo_root).resolve() / "config" / "generation_guardrails.json"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _normalize_string_list(value: Any) -> list[str]:
    if isinstance(value, (list, tuple)):
        seen: set[str] = set()
        normalized: list[str] = []
        for item in value:
            text = str(item).strip()
            if not text or text in seen:
                continue
            seen.add(text)
            normalized.append(text)
        return normalized
    return []


def _normalize_phrase_map(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, str] = {}
    for raw_key, raw_value in value.items():
        key = str(raw_key).strip()
        if not key:
            continue
        value_text = str(raw_value).strip()
        normalized[key] = value_text or key
    return normalized


def _normalize_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _preset_scope_keys(family: str, preset: str) -> list[str]:
    family_name = str(family).strip()
    preset_name = str(preset).strip()
    keys: list[str] = []
    for candidate in (
        f"{family_name}/{preset_name}",
        f"{family_name}/{preset_name.rsplit('__', 1)[0]}" if "__" in preset_name else "",
    ):
        if candidate and candidate not in keys:
            keys.append(candidate)
    return keys


def prompt_guardrails_for(policy: dict[str, Any], family: str, preset: str) -> dict[str, Any]:
    prompt_guardrails = policy.get("prompt_guardrails", {})
    if not isinstance(prompt_guardrails, dict):
        return {
            "banned_phrases": {},
            "raw_prompt_banned_phrases": {},
            "required_phrases": [],
        }
    merged: dict[str, Any] = {
        "banned_phrases": {},
        "raw_prompt_banned_phrases": {},
        "required_phrases": [],
    }

    def merge_scope(raw_scope: Any) -> None:
        scope = raw_scope if isinstance(raw_scope, dict) else {}
        merged["banned_phrases"].update(_normalize_phrase_map(scope.get("banned_phrases")))
        merged["raw_prompt_banned_phrases"].update(_normalize_phrase_map(scope.get("raw_prompt_banned_phrases")))
        for phrase in _normalize_string_list(scope.get("required_phrases")):
            if phrase not in merged["required_phrases"]:
                merged["required_phrases"].append(phrase)

    families = prompt_guardrails.get("families", {})
    presets = prompt_guardrails.get("presets", {})
    if isinstance(families, dict):
        merge_scope(families.get(str(family).strip()))
    if isinstance(presets, dict):
        for key in _preset_scope_keys(family, preset):
            merge_scope(presets.get(key))
    return merged


def visual_qc_policy_for(policy: dict[str, Any], family: str, preset: str) -> dict[str, Any]:
    visual_qc = policy.get("visual_qc", {})
    if not isinstance(visual_qc, dict):
        return {}
    merged: dict[str, Any] = {}
    families = visual_qc.get("families", {})
    presets = visual_qc.get("presets", {})
    if isinstance(families, dict):
        family_policy = families.get(str(family).strip(), {})
        if isinstance(family_policy, dict):
            merged.update(family_policy)
    if isinstance(presets, dict):
        for key in _preset_scope_keys(family, preset):
            preset_policy = presets.get(key, {})
            if isinstance(preset_policy, dict):
                merged.update(preset_policy)
    return merged


def semantic_qc_profile_for(
    policy: dict[str, Any],
    *,
    family: str,
    preset: str,
    profile_name: str = "",
) -> dict[str, Any]:
    visual_policy = visual_qc_policy_for(policy, family, preset)
    requested_profile = str(profile_name or visual_policy.get("semantic_qc_profile", "")).strip()
    semantic_qc = policy.get("semantic_qc", {})
    if not isinstance(semantic_qc, dict):
        return {}
    profiles = semantic_qc.get("profiles", {})
    if not isinstance(profiles, dict) or not requested_profile:
        return {}
    raw_profile = profiles.get(requested_profile, {})
    if not isinstance(raw_profile, dict):
        return {}

    weights = raw_profile.get("weights", {})
    weight_map = weights if isinstance(weights, dict) else {}
    stage_focus = raw_profile.get("stage_focus", {})
    stage_focus_map = stage_focus if isinstance(stage_focus, dict) else {}
    default_model = str(semantic_qc.get("default_model", "")).strip()
    return {
        "name": requested_profile,
        "model": str(raw_profile.get("model", "")).strip() or default_model,
        "brief": str(raw_profile.get("brief", "")).strip(),
        "allowed_issue_tags": _normalize_string_list(raw_profile.get("allowed_issue_tags")),
        "hard_fail_tags": _normalize_string_list(raw_profile.get("hard_fail_tags")),
        "minimum_rank_score": _normalize_float(raw_profile.get("minimum_rank_score"), 0.0),
        "minimum_composition_score": _normalize_float(raw_profile.get("minimum_composition_score"), 0.0),
        "weights": {
            "composition": _normalize_float(weight_map.get("composition"), 0.65),
            "clarity": _normalize_float(weight_map.get("clarity"), 0.35),
            "anchor_bonus_clear": _normalize_float(weight_map.get("anchor_bonus_clear"), 2.0),
            "anchor_bonus_partial": _normalize_float(weight_map.get("anchor_bonus_partial"), 0.5),
            "anchor_penalty_missing": _normalize_float(weight_map.get("anchor_penalty_missing"), 3.0),
            "issue_penalty": _normalize_float(weight_map.get("issue_penalty"), 1.5),
        },
        "stage_focus": {
            "candidate": str(stage_focus_map.get("candidate", "")).strip(),
            "final": str(stage_focus_map.get("final", "")).strip(),
        },
    }


def motion_guardrails_for(
    policy: dict[str, Any],
    *,
    episode_id: str,
    motion_item_id: str,
    preset_id: str = "",
) -> dict[str, Any]:
    motion = policy.get("motion", {})
    payload = motion if isinstance(motion, dict) else {}
    min_duration_seconds = float(payload.get("default_min_duration_seconds", 0.0) or 0.0)
    entries = payload.get("entries", [])
    if isinstance(entries, list):
        for raw_entry in entries:
            entry = raw_entry if isinstance(raw_entry, dict) else {}
            if str(entry.get("episode_id", "")).strip() != str(episode_id).strip():
                continue
            if str(entry.get("motion_item_id", "")).strip() != str(motion_item_id).strip():
                continue
            configured_preset_id = str(entry.get("preset_id", "")).strip()
            if configured_preset_id and preset_id and configured_preset_id != str(preset_id).strip():
                continue
            min_duration_seconds = max(min_duration_seconds, float(entry.get("min_duration_seconds", 0.0) or 0.0))
            break
    return {
        "min_duration_seconds": min_duration_seconds,
    }


__all__ = [
    "load_guardrail_policy",
    "motion_guardrails_for",
    "prompt_guardrails_for",
    "semantic_qc_profile_for",
    "visual_qc_policy_for",
]
