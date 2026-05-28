from __future__ import annotations

from pathlib import Path


class AudioRepo:
    FLOW_STEPS = ("validate", "cost", "render", "guard", "merge", "qa", "promote-audio")

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    @property
    def pipeline_script(self) -> Path:
        return self.root / "scripts" / "cascade_tts_pipeline.sh"

    @property
    def transcript_output_dir(self) -> Path:
        return self.root / "tmp" / "transcripts_final"

    def pipeline_dir(self, audio_pipeline_alias: str) -> Path:
        return self.root / "tmp" / audio_pipeline_alias

    def guard_dir(self, pipeline_dir: str | Path) -> Path:
        return Path(pipeline_dir) / "prosody_guard"

    def mastering_dir(self, pipeline_dir: str | Path) -> Path:
        return Path(pipeline_dir) / "mastering"

    def package_metadata_path(self, pipeline_dir: str | Path) -> Path:
        return Path(pipeline_dir) / "audio_package.json"
