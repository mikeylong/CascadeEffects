from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import textwrap
import unittest
import wave
from pathlib import Path


REPO_ROOT = Path("/Users/mike/CascadeEffects/packages/media-pipeline/audio")
PIPELINE_SCRIPT = REPO_ROOT / "scripts" / "cascade_tts_pipeline.sh"
TEST_ELEVENLABS_DEFAULT_MODEL = "test_model_v2_hq"


def _write_wav(path: Path, *, frames: int = 4410) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(44100)
        handle.writeframes(b"\x00\x00" * frames)


def _write_fake_transcribe(bin_dir: Path) -> Path:
    script_path = bin_dir / "transcribe"
    script_path.write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env python3
            import sys
            from pathlib import Path

            args = sys.argv[1:]
            out_dir = None
            for index, token in enumerate(args):
                if token == "-o" and index + 1 < len(args):
                    out_dir = Path(args[index + 1])
                    break
            if out_dir is None:
                raise SystemExit("missing -o")
            target = Path(args[-1])
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / f"{target.stem}.diarized.txt").write_text("transcript\\n", encoding="utf-8")
            """
        ),
        encoding="utf-8",
    )
    script_path.chmod(0o755)
    return script_path


@unittest.skipUnless(
    shutil.which("ffmpeg") and shutil.which("ffprobe") and shutil.which("uv"),
    "ffmpeg, ffprobe, and uv are required",
)
class CascadeTtsPipelineTests(unittest.TestCase):
    def _episode_dir(self, root: Path, episode_name: str = "Ep99_Test") -> Path:
        episode_dir = root / episode_name
        episode_dir.mkdir(parents=True, exist_ok=True)
        (episode_dir / f"{episode_name}.txt").write_text("[calm] Test narration.\n", encoding="utf-8")
        return episode_dir

    def _final_jobs_manifest(self, pipeline_dir: Path) -> Path:
        manifest_path = pipeline_dir / "final_jobs.jsonl"
        manifest_path.write_text(
            json.dumps(
                {
                    "out": "chunk_01.wav",
                    "voice": "cedar",
                    "response_format": "wav",
                    "input": "Test narration.",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return manifest_path

    def _run(self, command: str, *, env: dict[str, str], cwd: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(PIPELINE_SCRIPT), command],
            cwd=str(cwd),
            env=env,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def _base_env(self, temp_root: Path, *, provider: str | None = "openai") -> dict[str, str]:
        pipeline_dir = temp_root / "pipeline"
        render_dir = pipeline_dir / "rendered"
        render_dir.mkdir(parents=True, exist_ok=True)
        _write_wav(render_dir / "chunk_01.wav")

        episode_dir = self._episode_dir(temp_root)
        transcript_out_dir = pipeline_dir / "transcripts"
        master_out = pipeline_dir / "master.wav"
        premaster_out = pipeline_dir / "premaster.wav"
        final_jobs = self._final_jobs_manifest(pipeline_dir)

        bin_dir = temp_root / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        _write_fake_transcribe(bin_dir)
        voice_profile_registry = temp_root / "youtube_shorts_voice_profiles.json"
        voice_profile_registry.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "profiles": {
                        "youtube_shorts_mike_challenger_match_v1": {
                            "provider": "elevenlabs",
                            "voice": "voice_test_123",
                            "model": TEST_ELEVENLABS_DEFAULT_MODEL,
                            "final_export_eligible": True,
                            "render_settings": {
                                "stability": 0.6,
                                "similarity_boost": 0.8,
                                "style": 0.0,
                                "use_speaker_boost": True,
                                "speed": 0.95,
                            },
                        },
                        "openai_cedar_legacy_v1": {
                            "provider": "openai",
                            "voice": "cedar",
                            "model": "gpt-4o-mini-tts-2025-12-15",
                            "final_export_eligible": False,
                            "render_settings": {},
                        },
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        env = os.environ.copy()
        env.update(
            {
                "PIPELINE_DIR": str(pipeline_dir),
                "FINAL_JOBS": str(final_jobs),
                "RENDER_OUT_DIR": str(render_dir),
                "MASTER_OUT": str(master_out),
                "PREMASTER_OUT": str(premaster_out),
                "MASTERING_ENABLED": "0",
                "EPISODE_DIR": str(episode_dir),
                "TRANSCRIPT_OUT_DIR": str(transcript_out_dir),
                "VOICE": "cedar",
                "ELEVENLABS_DEFAULT_MODEL": TEST_ELEVENLABS_DEFAULT_MODEL,
                "SHORTS_VOICE_PROFILE_REGISTRY": str(voice_profile_registry),
                "ENV_FILE": str(temp_root / ".env.local"),
                "PATH": f"{bin_dir}:{env.get('PATH', '')}",
            }
        )
        if provider is not None:
            env["TTS_PROVIDER"] = provider
        else:
            env.pop("TTS_PROVIDER", None)
        return env

    def test_openai_merge_and_qa_write_audio_package_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            env = self._base_env(temp_root, provider="openai")

            self._run("merge", env=env, cwd=temp_root)
            self._run("qa", env=env, cwd=temp_root)

            metadata_path = temp_root / "pipeline" / "audio_package.json"
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
            episode_name = "Ep99_Test"
            self.assertEqual(payload["provider"], "openai")
            self.assertEqual(payload["voice"], "cedar")
            self.assertEqual(payload["model"], "gpt-4o-mini-tts-2025-12-15")
            self.assertEqual(payload["voice_profile_id"], "openai_cedar_legacy_v1")
            self.assertFalse(payload["voice_profile_final_export_eligible"])
            self.assertEqual(payload["render_settings"]["provider"], "openai")
            self.assertEqual(payload["effective_manifest_path"], str(temp_root / "pipeline" / "final_jobs.jsonl"))
            self.assertEqual(payload["packaged_path"], str(temp_root / episode_name / "final" / f"{episode_name}.wav"))
            self.assertTrue(payload["packaged_sha256"])
            self.assertTrue(payload["packaged_at"])
            self.assertEqual(payload["transcript_path"], str(temp_root / "pipeline" / "transcripts" / f"{episode_name}.diarized.txt"))
            self.assertTrue(payload["transcript_sha256"])
            self.assertTrue(payload["qa_completed_at"])

    def test_elevenlabs_merge_and_qa_write_audio_package_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            env = self._base_env(temp_root, provider="elevenlabs")
            env["ELEVEN_LABS_VOICE_ID"] = "voice_test_123"
            effective_manifest = temp_root / "pipeline" / "effective_final_jobs.elevenlabs.jsonl"
            effective_manifest.write_text(
                json.dumps(
                    {
                        "out": "chunk_01.wav",
                        "voice": "cedar",
                        "response_format": "wav",
                        "input": "Test narration.",
                        "elevenlabs_text": "[calm] Test narration.",
                        "elevenlabs_model_id": TEST_ELEVENLABS_DEFAULT_MODEL,
                        "elevenlabs_seed": 123,
                        "elevenlabs_apply_text_normalization": "on",
                        "elevenlabs_voice_settings": {"speed": 0.95, "stability": 0.6},
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            self._run("merge", env=env, cwd=temp_root)
            self._run("qa", env=env, cwd=temp_root)

            metadata_path = temp_root / "pipeline" / "audio_package.json"
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["provider"], "elevenlabs")
            self.assertEqual(payload["voice"], "voice_test_123")
            self.assertEqual(payload["model"], TEST_ELEVENLABS_DEFAULT_MODEL)
            self.assertEqual(payload["voice_profile_id"], "youtube_shorts_mike_challenger_match_v1")
            self.assertTrue(payload["voice_profile_final_export_eligible"])
            self.assertEqual(payload["voice_profile_settings"]["speed"], 0.95)
            self.assertEqual(payload["render_settings"]["speed"], 0.95)
            self.assertEqual(payload["render_settings"]["elevenlabs_seed"], 123)
            self.assertEqual(payload["effective_manifest_path"], str(effective_manifest))
            self.assertTrue(payload["transcript_path"].endswith("Ep99_Test.diarized.txt"))
            self.assertTrue(payload["qa_completed_at"])

    def test_default_provider_is_elevenlabs_when_tts_provider_is_unset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            env = self._base_env(temp_root, provider=None)
            env["ELEVEN_LABS_VOICE_ID"] = "voice_test_123"
            effective_manifest = temp_root / "pipeline" / "effective_final_jobs.elevenlabs.jsonl"
            effective_manifest.write_text(
                json.dumps(
                    {
                        "out": "chunk_01.wav",
                        "voice": "cedar",
                        "response_format": "wav",
                        "input": "Test narration.",
                        "elevenlabs_text": "[calm] Test narration.",
                        "elevenlabs_model_id": TEST_ELEVENLABS_DEFAULT_MODEL,
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            self._run("merge", env=env, cwd=temp_root)
            self._run("qa", env=env, cwd=temp_root)

            payload = json.loads((temp_root / "pipeline" / "audio_package.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["provider"], "elevenlabs")
            self.assertEqual(payload["model"], TEST_ELEVENLABS_DEFAULT_MODEL)

    def test_default_elevenlabs_cost_requires_configured_model(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            env = self._base_env(temp_root, provider=None)
            env.pop("ELEVENLABS_DEFAULT_MODEL", None)

            completed = subprocess.run(
                ["bash", str(PIPELINE_SCRIPT), "cost"],
                cwd=str(temp_root),
                env=env,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("ELEVENLABS_DEFAULT_MODEL is not set", completed.stderr)

    def test_compile_only_cost_manifest_does_not_create_promotable_package_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            env = self._base_env(temp_root, provider="elevenlabs")
            env["ELEVEN_LABS_VOICE_ID"] = "voice_test_123"

            self._run("cost", env=env, cwd=temp_root)

            self.assertTrue((temp_root / "pipeline" / "effective_cost_final_jobs.elevenlabs.jsonl").exists())
            self.assertFalse((temp_root / "pipeline" / "audio_package.json").exists())


if __name__ == "__main__":
    unittest.main()
