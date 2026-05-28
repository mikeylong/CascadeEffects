from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return re.sub(r"-{2,}", "-", slug)


def compact_slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def humanize_episode_name(fragment: str) -> str:
    if "-" in fragment and any(char.isdigit() for char in fragment):
        return fragment
    return fragment.replace("-", " ")


def find_primary_file(directory: Path, pattern: str) -> Path | None:
    matches = sorted(directory.glob(pattern))
    return matches[0] if matches else None


@dataclass(frozen=True)
class EpisodeDirectoryInfo:
    directory: Path
    number: int
    title_fragment: str
    episode_id: str
    title: str
    folder_name: str
    script_path: Path
    canonical_final_audio_path: Path
    detected_final_audio_path: Path | None
    visual_research_dir: Path
    visual_research_paths: dict[str, Path]
    fact_check_path: Path | None

    @property
    def packaged_final_exists(self) -> bool:
        return self.canonical_final_audio_path.exists()


class EpisodesRepo:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def list_episode_directories(self) -> list[Path]:
        return sorted(path for path in self.root.glob("Ep*_*") if path.is_dir())

    def parse_episode_directory(self, path: Path) -> EpisodeDirectoryInfo:
        match = re.match(r"^Ep(?P<number>\d+)_(?P<title>.+)$", path.name)
        if not match:
            raise SystemExit(f"Unsupported episode directory name: {path.name}")
        number = int(match.group("number"))
        title_fragment = match.group("title")
        episode_id = slugify(title_fragment)
        title = humanize_episode_name(title_fragment).replace("_", " ").title()
        script_path = path / f"{path.name}.txt"
        if not script_path.exists():
            script_path = find_primary_file(path, "*.txt") or script_path
        canonical_final_audio_path = path / "final" / f"{path.name}.wav"
        detected_final_audio_path: Path | None = canonical_final_audio_path if canonical_final_audio_path.exists() else None
        if detected_final_audio_path is None:
            detected_final_audio_path = find_primary_file(path / "final", "*.wav")
        visual_research_dir = path / "visual_research"
        fact_check_path = path / "fact_check.md"
        return EpisodeDirectoryInfo(
            directory=path,
            number=number,
            title_fragment=title_fragment,
            episode_id=episode_id,
            title=title,
            folder_name=path.name,
            script_path=script_path,
            canonical_final_audio_path=canonical_final_audio_path,
            detected_final_audio_path=detected_final_audio_path,
            visual_research_dir=visual_research_dir,
            visual_research_paths={
                "contact_sheet_path": visual_research_dir / "contact_sheet.pdf",
                "source_inventory_path": visual_research_dir / "source_inventory.json",
                "act_breakdown_path": visual_research_dir / "act_breakdown.md",
                "reference_notes_path": visual_research_dir / "reference_notes.md",
                "sources_path": visual_research_dir / "sources.md",
                "assembly_notes_path": visual_research_dir / "assembly_notes.md",
            },
            fact_check_path=fact_check_path if fact_check_path.exists() else None,
        )

    def get_episode_info(self, episode_id: str) -> EpisodeDirectoryInfo | None:
        needle = episode_id.strip().lower()
        for directory in self.list_episode_directories():
            info = self.parse_episode_directory(directory)
            if info.episode_id == needle:
                return info
        return None

    def resolve_episode_directories(self, episode: str | None, select_all: bool) -> list[Path]:
        directories = self.list_episode_directories()
        if select_all:
            return directories
        if not episode:
            raise SystemExit("--episode or --all is required.")
        needle = episode.strip().lower()
        for directory in directories:
            info = self.parse_episode_directory(directory)
            candidates = {
                directory.name.lower(),
                info.episode_id,
                str(info.number),
                f"ep{info.number}",
                f"episode-{info.number:02d}",
            }
            if needle in candidates:
                return [directory]
        raise SystemExit(f"Unknown episode folder or id: {episode}")
