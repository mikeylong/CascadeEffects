from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MotionCertificationEntry:
    episode_id: str
    motion_item_id: str
    preset_id: str
    still_path: Path
    prompt: str
    frames: int
    width: int
    height: int
    pipeline: str
    typography_intent_path: Path | None
    expected_typography_metadata: bool
    min_duration_seconds: float


@dataclass(frozen=True)
class TextGovernanceEntry:
    family: str
    preset: str
    canonical_seed: int
    governance_class: str
    source_text_repair_mode: str
    typography_mode: str
    handoff_probe: str
    handoff_typography_intent_path: Path | None
    handoff_frames: int
    width: int
    height: int
    expected_typography_metadata: bool


class VizRepo:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self._motion_certifications: dict[tuple[str, str], MotionCertificationEntry] | None = None
        self._text_governance: dict[tuple[str, str], TextGovernanceEntry] | None = None
        self._generation_guardrails: dict[str, Any] | None = None

    def spec_exists(self, family: str, preset: str) -> bool:
        spec_dir = self.root / "workflows" / "specs" / family
        return any(spec_dir.glob(f"{preset}__*.json"))

    def _load_json(self, path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def _resolve_repo_relative_path(self, raw: str) -> Path | None:
        candidate = raw.strip()
        if not candidate:
            return None
        path = Path(candidate)
        if path.is_absolute():
            return path
        return self.root / path

    def motion_certifications(self) -> dict[tuple[str, str], MotionCertificationEntry]:
        if self._motion_certifications is None:
            path = self.root / "config" / "motion_certification_matrix.json"
            entries: dict[tuple[str, str], MotionCertificationEntry] = {}
            if path.exists():
                for raw in self._load_json(path).get("entries", []):
                    entry = MotionCertificationEntry(
                        episode_id=str(raw["episode_id"]),
                        motion_item_id=str(raw["motion_item_id"]),
                        preset_id=str(raw["preset_id"]),
                        still_path=Path(str(raw["still_path"])),
                        prompt=str(raw["prompt"]),
                        frames=int(raw["frames"]),
                        width=int(raw["width"]),
                        height=int(raw["height"]),
                        pipeline=str(raw["pipeline"]),
                        typography_intent_path=self._resolve_repo_relative_path(str(raw.get("typography_intent_path", ""))),
                        expected_typography_metadata=bool(raw["expected_typography_metadata"]),
                        min_duration_seconds=float(raw.get("min_duration_seconds", 0.0) or 0.0),
                    )
                    entries[(entry.episode_id, entry.motion_item_id)] = entry
            self._motion_certifications = entries
        return self._motion_certifications

    def text_governance(self) -> dict[tuple[str, str], TextGovernanceEntry]:
        if self._text_governance is None:
            path = self.root / "config" / "text_governance_matrix.json"
            entries: dict[tuple[str, str], TextGovernanceEntry] = {}
            if path.exists():
                for raw in self._load_json(path).get("entries", []):
                    entry = TextGovernanceEntry(
                        family=str(raw["family"]),
                        preset=str(raw["preset"]),
                        canonical_seed=int(raw["canonical_seed"]),
                        governance_class=str(raw["governance_class"]),
                        source_text_repair_mode=str(raw["source_text_repair_mode"]),
                        typography_mode=str(raw["typography_mode"]),
                        handoff_probe=str(raw["handoff_probe"]),
                        handoff_typography_intent_path=self._resolve_repo_relative_path(
                            str(raw.get("handoff_typography_intent_path", ""))
                        ),
                        handoff_frames=int(raw["handoff_frames"]),
                        width=int(raw["width"]),
                        height=int(raw["height"]),
                        expected_typography_metadata=bool(raw["expected_typography_metadata"]),
                    )
                    entries[(entry.family, entry.preset)] = entry
            self._text_governance = entries
        return self._text_governance

    def generation_guardrails(self) -> dict[str, Any]:
        if self._generation_guardrails is None:
            path = self.root / "config" / "generation_guardrails.json"
            payload = self._load_json(path) if path.exists() else {}
            self._generation_guardrails = payload if isinstance(payload, dict) else {}
        return self._generation_guardrails

    def repair_policy_path(self, family: str, preset: str) -> Path | None:
        family_name = str(family).strip()
        preset_name = str(preset).strip()
        if not family_name or not preset_name:
            return None
        candidate = self.root / "workflows" / "source_text_repair" / family_name / f"{preset_name}.json"
        return candidate if candidate.exists() else None

    def shared_research_source_repair_policy_path(self) -> Path | None:
        candidate = self.root / "workflows" / "source_text_repair" / "shared" / "research_source.json"
        return candidate if candidate.exists() else None

    @staticmethod
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

    @staticmethod
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

    def allowed_reject_tags(self, gate_type: str) -> list[str]:
        gate_types = self.generation_guardrails().get("gate_types", {})
        if not isinstance(gate_types, dict):
            return []
        return self._normalize_string_list(gate_types.get(str(gate_type).strip(), ()))

    def reject_tag_policy(self, tag: str) -> dict[str, Any]:
        reject_tags = self.generation_guardrails().get("reject_tags", {})
        if not isinstance(reject_tags, dict):
            return {}
        payload = reject_tags.get(str(tag).strip(), {})
        return payload if isinstance(payload, dict) else {}

    def reject_tag_mode(self, tag: str) -> str:
        mode = str(self.reject_tag_policy(tag).get("mode", "")).strip()
        return mode or "review_only"

    def reject_tag_label(self, tag: str) -> str:
        label = str(self.reject_tag_policy(tag).get("label", "")).strip()
        return label or str(tag).strip().replace("_", " ")

    def reject_tag_options(self, gate_type: str) -> list[dict[str, str]]:
        options: list[dict[str, str]] = []
        for tag in self.allowed_reject_tags(gate_type):
            options.append(
                {
                    "tag": tag,
                    "label": self.reject_tag_label(tag),
                    "mode": self.reject_tag_mode(tag),
                }
            )
        return options

    def find_prompt_guardrails(self, family: str, preset: str) -> dict[str, Any]:
        prompt_guardrails = self.generation_guardrails().get("prompt_guardrails", {})
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
            merged["banned_phrases"].update(self._normalize_phrase_map(scope.get("banned_phrases")))
            merged["raw_prompt_banned_phrases"].update(self._normalize_phrase_map(scope.get("raw_prompt_banned_phrases")))
            for phrase in self._normalize_string_list(scope.get("required_phrases")):
                if phrase not in merged["required_phrases"]:
                    merged["required_phrases"].append(phrase)

        families = prompt_guardrails.get("families", {})
        presets = prompt_guardrails.get("presets", {})
        if isinstance(families, dict):
            merge_scope(families.get(str(family).strip()))
        if isinstance(presets, dict):
            family_name = str(family).strip()
            preset_name = str(preset).strip()
            preset_keys = [f"{family_name}/{preset_name}"]
            if "__" in preset_name:
                preset_keys.append(f"{family_name}/{preset_name.rsplit('__', 1)[0]}")
            for preset_key in preset_keys:
                merge_scope(presets.get(preset_key))
        return merged

    def find_visual_qc_policy(self, family: str, preset: str) -> dict[str, Any]:
        visual_qc = self.generation_guardrails().get("visual_qc", {})
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
            family_name = str(family).strip()
            preset_name = str(preset).strip()
            preset_keys = [f"{family_name}/{preset_name}"]
            if "__" in preset_name:
                preset_keys.append(f"{family_name}/{preset_name.rsplit('__', 1)[0]}")
            for preset_key in preset_keys:
                preset_policy = presets.get(preset_key, {})
                if isinstance(preset_policy, dict):
                    merged.update(preset_policy)
        return merged

    def find_motion_guardrails(
        self,
        episode_id: str,
        motion_item_id: str,
        *,
        preset_id: str = "",
    ) -> dict[str, Any]:
        certification = self.find_motion_certification(episode_id, motion_item_id)
        motion_guardrails = self.generation_guardrails().get("motion", {})
        payload = motion_guardrails if isinstance(motion_guardrails, dict) else {}
        default_min_duration = float(payload.get("default_min_duration_seconds", 0.0) or 0.0)
        entry_min_duration = 0.0
        entries = payload.get("entries", [])
        if isinstance(entries, list):
            for raw_entry in entries:
                entry = raw_entry if isinstance(raw_entry, dict) else {}
                if str(entry.get("episode_id", "")).strip() != str(episode_id).strip():
                    continue
                if str(entry.get("motion_item_id", "")).strip() != str(motion_item_id).strip():
                    continue
                raw_preset_id = str(entry.get("preset_id", "")).strip()
                if raw_preset_id and preset_id and raw_preset_id != str(preset_id).strip():
                    continue
                entry_min_duration = float(entry.get("min_duration_seconds", 0.0) or 0.0)
                break
        certification_min_duration = float(certification.min_duration_seconds) if certification else 0.0
        return {
            "min_duration_seconds": max(default_min_duration, entry_min_duration, certification_min_duration),
        }

    def find_motion_certification(self, episode_id: str, motion_item_id: str) -> MotionCertificationEntry | None:
        return self.motion_certifications().get((episode_id, motion_item_id))

    def find_text_governance(self, family: str, preset: str) -> TextGovernanceEntry | None:
        return self.text_governance().get((family, preset))
