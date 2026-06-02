from __future__ import annotations

import argparse
import contextlib
import importlib.machinery
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CE_PATH = REPO_ROOT / "bin" / "ce"


def load_ce_module():
    loader = importlib.machinery.SourceFileLoader("ce_cli_under_test", str(CE_PATH))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[loader.name] = module
    loader.exec_module(module)
    return module


ce = load_ce_module()


class CeAudioCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.original_root = ce.ROOT
        self.original_artifact_root = ce.ARTIFACT_ROOT
        ce.ROOT = self.root
        ce.ARTIFACT_ROOT = self.root / ".artifacts"
        self.episode_dir = self.root / "episodes" / "season-02" / "ep-test"
        (self.episode_dir / "source").mkdir(parents=True)
        (self.episode_dir / "receipts").mkdir()
        (self.episode_dir / "reviews").mkdir()
        (self.episode_dir / "episode.toml").write_text(
            "\n".join(
                [
                    'schema_version = 1',
                    'season = "season-02"',
                    'episode_id = "ep-test"',
                    'title = "Test Episode"',
                    "",
                    "[gates]",
                    'human_script_approval_for_audio = "pass"',
                    'audio_keep = "pending"',
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (self.episode_dir / "state.json").write_text(
            json.dumps({"current_stage": "audio_keep"}) + "\n",
            encoding="utf-8",
        )
        (self.episode_dir / "tasks.jsonl").write_text(
            json.dumps({"task_id": "ep-test-audio-keep", "gate": "audio_keep", "status": "pending"}) + "\n",
            encoding="utf-8",
        )
        self.script_path = self.episode_dir / "source" / "longform-script.md"
        self.script_path.write_text(
            "\n".join(
                [
                    "# Longform Script: Test Episode",
                    "",
                    "status: review_ready",
                    "episode_id: ep-test",
                    "",
                    "## Cold Open",
                    "",
                    "The warning was visible before the system moved.",
                    "",
                    "The second paragraph keeps the chunker honest.",
                    "",
                    "## Review Notes",
                    "",
                    "Do not render this note.",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        self.preflight_note = self.episode_dir / "source" / "elevenlabs-preflight.md"
        self.preflight_note.write_text("preflight ok\n", encoding="utf-8")
        self.script_sha = ce.sha256(self.script_path)
        self.preflight_receipt = self.episode_dir / "receipts" / "elevenlabs-preflight.json"
        self.preflight_receipt.write_text(
            json.dumps(
                {
                    "status": "pass",
                    "script_sha256_current": self.script_sha,
                    "script_sha256_reviewed": self.script_sha,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        self.approval_receipt = self.episode_dir / "receipts" / "human-script-approval-for-audio.json"
        self.approval_receipt.write_text(
            json.dumps(
                {
                    "status": "pass",
                    "script_sha256_reviewed": self.script_sha,
                    "audio_render_authorized": True,
                    "reads": {"audio_render_authorized": True},
                }
            )
            + "\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        ce.ROOT = self.original_root
        ce.ARTIFACT_ROOT = self.original_artifact_root
        self.tmp.cleanup()

    def make_package(self, *, source_sha: str | None = None, transcript: bool = True, outside_audio: bool = False) -> Path:
        artifact_dir = ce.ARTIFACT_ROOT / "season-02" / "ep-test" / "audio" / self.script_sha[:12]
        artifact_dir.mkdir(parents=True)
        audio_path = (self.root / "outside.wav") if outside_audio else (artifact_dir / "longform-narration.wav")
        audio_path.write_bytes(b"fake wav")
        transcript_path = artifact_dir / "transcript-qa" / "longform-narration.diarized.txt"
        if transcript:
            transcript_path.parent.mkdir(parents=True)
            transcript_path.write_text("The warning was visible.\n", encoding="utf-8")
        package_path = artifact_dir / "audio-package.json"
        package = {
            "provider": "elevenlabs",
            "model": "eleven_multilingual_v2",
            "source_script_sha256": source_sha or self.script_sha,
            "source_script_path": "episodes/season-02/ep-test/source/longform-script.md",
            "master_audio_path": ce.safe_rel(audio_path),
            "master_audio_sha256": ce.sha256(audio_path),
            "chunk_count": 1,
        }
        if transcript:
            package["transcript_txt_path"] = ce.safe_rel(transcript_path)
            package["transcript_txt_sha256"] = ce.sha256(transcript_path)
        package_path.write_text(json.dumps(package, indent=2) + "\n", encoding="utf-8")
        return package_path

    def test_resolve_episode_dir_from_root_episode_and_nested_cwd(self) -> None:
        self.assertEqual(ce.resolve_episode_dir("ep-test"), self.episode_dir)
        self.assertEqual(ce.resolve_episode_dir(cwd=self.episode_dir), self.episode_dir)
        self.assertEqual(ce.resolve_episode_dir(cwd=self.episode_dir / "source"), self.episode_dir)

    def test_build_audio_env_writes_script_hash_scoped_manifest(self) -> None:
        ctx = ce.resolve_episode_context("ep-test")
        env, artifact_dir = ce.build_season2_audio_env(ctx)
        self.assertEqual(Path(env["EPISODE_SCRIPT"]), self.script_path)
        self.assertEqual(Path(env["EPISODE_FINAL_OUT"]), artifact_dir / "longform-narration.wav")
        self.assertEqual(Path(env["AUDIO_PACKAGE_PATH"]), artifact_dir / "audio-package.json")
        self.assertIn(self.script_sha[:12], str(artifact_dir))

        jobs_path = Path(env["FINAL_JOBS"])
        jobs = [json.loads(line) for line in jobs_path.read_text(encoding="utf-8").splitlines()]
        self.assertGreaterEqual(len(jobs), 1)
        combined_input = "\n\n".join(job["input"] for job in jobs)
        self.assertIn("Test Episode", combined_input)
        self.assertIn("The warning was visible", combined_input)
        self.assertNotIn("status: review_ready", combined_input)
        self.assertNotIn("Do not render this note", combined_input)
        self.assertEqual(jobs[0]["source_script_sha256"], self.script_sha)
        self.assertTrue(jobs[0]["out"].startswith("chunks/ep-test_chunk_"))

    def test_promote_audio_validation_rejects_missing_transcript(self) -> None:
        ctx = ce.resolve_episode_context("ep-test")
        package_path = self.make_package(transcript=False)
        with self.assertRaises(SystemExit):
            ce.validate_promotable_audio_package(ctx, package_path)

    def test_promote_audio_validation_rejects_script_hash_mismatch(self) -> None:
        ctx = ce.resolve_episode_context("ep-test")
        package_path = self.make_package(source_sha="0" * 64)
        with self.assertRaises(SystemExit):
            ce.validate_promotable_audio_package(ctx, package_path)

    def test_promote_audio_validation_rejects_audio_outside_artifacts(self) -> None:
        ctx = ce.resolve_episode_context("ep-test")
        package_path = self.make_package(outside_audio=True)
        with self.assertRaises(SystemExit):
            ce.validate_promotable_audio_package(ctx, package_path)

    def test_promote_audio_dry_run_does_not_mutate_gate(self) -> None:
        package_path = self.make_package()
        args = argparse.Namespace(episode_id="ep-test", package=str(package_path), dry_run=True)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(ce.promote_audio(args), 0)
        self.assertEqual(ce.read_gate_status(self.episode_dir / "episode.toml", "audio_keep"), "pending")


if __name__ == "__main__":
    unittest.main()
