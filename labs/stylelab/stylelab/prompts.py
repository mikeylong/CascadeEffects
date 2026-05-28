from __future__ import annotations

from typing import Any


MODE_TO_MODEL_FAMILY = {
    "sketch": "flux2_klein_contract",
    "final": "flux2_dev_reference_contract",
    "lock": "kontext_lock_contract",
}


def _format_box(box: list[float]) -> str:
    return f"x={box[0]:.2f}-{box[2]:.2f}, y={box[1]:.2f}-{box[3]:.2f}"


def compile_negative_prompt(profile: dict[str, Any]) -> str:
    parts = [str(item).strip() for item in profile["negative_prompt_defaults"] if str(item).strip()]
    return ", ".join(parts)


def compile_style_profile(profile: dict[str, Any]) -> dict[str, Any]:
    rules = profile["rules"]
    contract = profile["contract_metrics"]
    canon = [
        str(profile["prompts"]["global_base"]).strip(),
        str(rules["subject_anchor"]).strip(),
        str(rules["reduction"]).strip(),
        str(rules["color_fields"]).strip(),
        str(rules["asymmetry"]).strip(),
        str(rules["selective_saturation"]).strip(),
        str(rules["textural_restraint"]).strip(),
        str(rules["implied_story"]).strip(),
        f"Maintain at least {int(float(contract['negative_space_ratio']['min']) * 100)}% negative space with an asymmetrical focal mass.",
        f"Use no more than {int(contract['max_palette_count'])} colors and only {int(contract['max_accent_colors'])} saturated accent.",
        f"Allow exactly {int(contract['surreal_breach_count'])} surreal breach and keep everything else coherent.",
        f"Lighting must remain {str(contract['lighting_style']).replace('_', ' ')}.",
        f"Do not include {', '.join(str(item) for item in contract['forbidden_elements'])}.",
    ]
    return {
        "id": str(profile["id"]),
        "palette": dict(profile["palette"]),
        "canon": [part for part in canon if part],
        "negative_prompt": compile_negative_prompt(profile),
        "contract_metrics": dict(contract),
        "caption_safe_defaults": dict(profile["caption_safe_defaults"]),
        "motion_presets": dict(profile["motion_presets"]),
    }


def compile_prompt(scene: dict[str, Any], profile: dict[str, Any], *, mode: str) -> str:
    prompts = profile["prompts"]
    compiled_profile = compile_style_profile(profile)
    anchor = scene["subject_anchor"]
    mass = scene["dominant_mass_strategy"]
    accent = scene["accent_strategy"]
    reflection = scene["reflection_strategy"]
    historical_anchor = scene["historical_anchor"]
    surreal_breach = scene["surreal_breach"]
    caption_safe_zone = scene.get("caption_safe_zone") or compiled_profile["caption_safe_defaults"]
    refs = ", ".join(ref["label"] for ref in scene["source_refs"])
    prompt_parts = [
        *compiled_profile["canon"],
        prompts["mode_overrides"][mode],
        f"Historical anchor: {historical_anchor['description']}.",
        f"Historical topic: {historical_anchor['topic']}.",
        f"Single surreal breach: {surreal_breach['description']}.",
        f"Caption safety: keep the top UI band clear at {_format_box(caption_safe_zone['top_ui'])} and keep critical subject matter out of the subtitle band at {_format_box(caption_safe_zone['subtitles'])}.",
        f"Hero subject: {anchor['description']}.",
        f"Subject archetype: {anchor['archetype']}.",
        f"Dominant mass: {mass['description']}.",
        f"Accent: {accent['description']}.",
        f"Reflection: {reflection['description']}.",
    ]
    if refs:
        prompt_parts.append(f"Source references carried forward as translated material only: {refs}.")
    else:
        prompt_parts.append("Single subject in mind only; no source references are used.")
    scene_intent = str(scene.get("prompt_overrides", {}).get("scene_intent", "")).strip()
    if scene_intent:
        prompt_parts.append(f"Scene intent: {scene_intent}.")
    return " ".join(part.strip() for part in prompt_parts if part.strip())


def model_family_for_mode(mode: str) -> str:
    return MODE_TO_MODEL_FAMILY[mode]
