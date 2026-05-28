from __future__ import annotations

from typing import Any


def compile_positive_prompt(scene: dict[str, Any]) -> str:
    parts = [str(scene["positive_style_prompt"]).strip(), str(scene["subject_prompt"]).strip()]
    return ", ".join(part for part in parts if part)


def compile_negative_prompt(scene: dict[str, Any]) -> str:
    return str(scene["negative_prompt"]).strip()


def scene_label(scene: dict[str, Any]) -> str:
    return f"{scene['incident']} {scene['variant'].upper()}"


def prompt_contract(scene: dict[str, Any]) -> dict[str, Any]:
    positive = compile_positive_prompt(scene)
    negative = compile_negative_prompt(scene)
    return {
        "positive_prompt": positive,
        "negative_prompt": negative,
        "incident": scene["incident"],
        "variant": scene["variant"],
    }
