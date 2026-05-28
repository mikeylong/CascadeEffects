from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LaunchEpisodeEntry:
    id: str
    title: str
    status: str
    label: str
    summary: str
    schedule_label: str
    schedule_value: str

    @property
    def homepage_visible(self) -> bool:
        return self.status == "recorded"


@dataclass(frozen=True)
class ChannelPillar:
    id: str
    title: str
    accent: str
    summary: str


def _extract_const_block(text: str, const_name: str) -> str:
    match = re.search(rf"export const {const_name}.*?=\s*\[(.*?)\];", text, re.DOTALL)
    return match.group(1) if match else ""


def _split_object_literals(block: str) -> list[str]:
    objects: list[str] = []
    depth = 0
    current: list[str] = []
    for char in block:
        if char == "{":
            depth += 1
        if depth > 0:
            current.append(char)
        if char == "}":
            depth -= 1
            if depth == 0 and current:
                objects.append("".join(current))
                current = []
    return objects


def _parse_single_quoted_field(block: str, field: str) -> str:
    match = re.search(rf"{field}\s*:\s*'((?:\\.|[^'])*)'", block, re.DOTALL)
    return match.group(1).replace("\\'", "'") if match else ""


def _normalize_label_fragment(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


class WebRepo:
    def __init__(self, site_facts_path: Path) -> None:
        self.site_facts_path = Path(site_facts_path)
        self._launch_entries: dict[str, LaunchEpisodeEntry] | None = None
        self._pillars: dict[str, ChannelPillar] | None = None

    def _read_site_facts(self) -> str:
        if not self.site_facts_path.exists():
            return ""
        return self.site_facts_path.read_text(encoding="utf-8")

    def launch_entries(self) -> dict[str, LaunchEpisodeEntry]:
        if self._launch_entries is None:
            text = self._read_site_facts()
            entries: dict[str, LaunchEpisodeEntry] = {}
            for block in _split_object_literals(_extract_const_block(text, "launchEpisodes")):
                entry = LaunchEpisodeEntry(
                    id=_parse_single_quoted_field(block, "id"),
                    title=_parse_single_quoted_field(block, "title"),
                    status=_parse_single_quoted_field(block, "status"),
                    label=_parse_single_quoted_field(block, "label"),
                    summary=_parse_single_quoted_field(block, "summary"),
                    schedule_label=_parse_single_quoted_field(block, "scheduleLabel"),
                    schedule_value=_parse_single_quoted_field(block, "scheduleValue"),
                )
                if entry.id:
                    entries[entry.id] = entry
            self._launch_entries = entries
        return self._launch_entries

    def channel_pillars(self) -> dict[str, ChannelPillar]:
        if self._pillars is None:
            text = self._read_site_facts()
            pillars: dict[str, ChannelPillar] = {}
            for block in _split_object_literals(_extract_const_block(text, "channelPillars")):
                pillar = ChannelPillar(
                    id=_parse_single_quoted_field(block, "id"),
                    title=_parse_single_quoted_field(block, "title"),
                    accent=_parse_single_quoted_field(block, "accent"),
                    summary=_parse_single_quoted_field(block, "summary"),
                )
                if pillar.id:
                    pillars[pillar.id] = pillar
            self._pillars = pillars
        return self._pillars

    def entry_ids(self) -> set[str]:
        return set(self.launch_entries())

    def get_launch_entry(self, episode_id: str) -> LaunchEpisodeEntry | None:
        return self.launch_entries().get(episode_id)

    def infer_pillar_id(self, label: str) -> str | None:
        category = label.split("·", 1)[0].strip()
        normalized = _normalize_label_fragment(category)
        for pillar in self.channel_pillars().values():
            pillar_normalized = _normalize_label_fragment(pillar.title)
            if pillar_normalized == normalized or normalized in pillar_normalized or pillar_normalized in normalized:
                return pillar.id
        return None
