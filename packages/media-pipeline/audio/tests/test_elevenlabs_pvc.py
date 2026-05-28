import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path("/Users/mike/CascadeEffects/packages/media-pipeline/audio")
SCRIPT_PATH = REPO_ROOT / "scripts" / "elevenlabs_pvc.py"
CONFIG_PATH = REPO_ROOT / "config" / "voice_profiles.toml"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ElevenLabsPvcTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module("elevenlabs_pvc", SCRIPT_PATH)

    def _run_main(self, argv: list[str]) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = self.mod.main(argv)
        return code, stdout.getvalue(), stderr.getvalue()

    def _mocked_common(self):
        return contextlib.ExitStack()

    def test_status_json_reports_missing_training_models_and_settings_drift(self):
        voice_payload = {
            "voice_id": "dPrTCMw2R7HQlznlgwCO",
            "category": "professional",
            "fine_tuning": {
                "state": {
                    "eleven_multilingual_v2": "fine_tuned",
                    "eleven_multilingual_sts_v2": "not_started",
                }
            },
            "settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True,
                "speed": 1.0,
            },
            "samples": [
                {
                    "sample_id": "sample_1",
                    "file_name": "11Labs.mp3",
                    "hash": "remotehash",
                    "duration_secs": 2464.917,
                    "remove_background_noise": False,
                }
            ],
        }

        with mock.patch.object(self.mod, "load_env_file_if_present"), mock.patch.object(
            self.mod, "_ensure_api_key", return_value="test-key"
        ), mock.patch.object(self.mod, "fetch_voice", return_value=voice_payload):
            code, stdout, stderr = self._run_main(
                [
                    "--config",
                    str(CONFIG_PATH),
                    "--env-file",
                    "/tmp/does-not-matter",
                    "status",
                    "--voice",
                    "mike",
                    "--json",
                ]
            )

        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        payload = json.loads(stdout)
        self.assertEqual(payload["voice_id"], "dPrTCMw2R7HQlznlgwCO")
        self.assertEqual(payload["sample_count"], 1)
        self.assertEqual(payload["missing_training_models"], ["eleven_multilingual_sts_v2"])
        self.assertEqual(payload["settings_drift"]["speed"]["local"], 0.95)
        self.assertEqual(payload["settings_drift"]["speed"]["remote"], 1.0)

    def test_sync_samples_uploads_missing_file_and_applies_manifest_updates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            samples_dir = temp_root / "samples"
            samples_dir.mkdir(parents=True, exist_ok=True)
            sample_path = samples_dir / "mike_take_01.wav"
            sample_path.write_bytes(b"RIFFtest-data")
            manifest_path = temp_root / "sample_manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "mike_take_01.wav": {
                            "remove_background_noise": True,
                            "trim_start": 120,
                            "trim_end": 980,
                            "notes": "trim the slate",
                        }
                    }
                ),
                encoding="utf-8",
            )

            uploaded_sample = {
                "sample_id": "sample_uploaded",
                "file_name": "mike_take_01.wav",
                "hash": "remote-hash",
                "remove_background_noise": True,
                "trim_start": None,
                "trim_end": None,
            }

            with mock.patch.object(self.mod, "load_env_file_if_present"), mock.patch.object(
                self.mod, "_ensure_api_key", return_value="test-key"
            ), mock.patch.object(
                self.mod, "fetch_voice", return_value={"voice_id": "dPrTCMw2R7HQlznlgwCO", "samples": []}
            ), mock.patch.object(
                self.mod, "upload_sample", return_value=uploaded_sample
            ) as upload_mock, mock.patch.object(self.mod, "update_sample", return_value={}) as update_mock:
                code, stdout, stderr = self._run_main(
                    [
                        "--config",
                        str(CONFIG_PATH),
                        "sync-samples",
                        "--voice",
                        "mike",
                        "--samples-dir",
                        str(samples_dir),
                        "--sample-manifest",
                        str(manifest_path),
                    ]
                )

            self.assertEqual(code, 0)
            self.assertEqual(stderr, "")
            upload_mock.assert_called_once()
            self.assertEqual(upload_mock.call_args.kwargs["remove_background_noise"], True)
            update_mock.assert_called_once_with(
                voice_id="dPrTCMw2R7HQlznlgwCO",
                sample_id="sample_uploaded",
                payload={"trim_start_time": 120, "trim_end_time": 980},
                api_key="test-key",
            )
            self.assertIn("Uploaded: 1", stdout)
            self.assertIn("Updated: 1", stdout)

    def test_sync_samples_dry_run_uses_filename_fallback_and_warns(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            samples_dir = temp_root / "samples"
            samples_dir.mkdir(parents=True, exist_ok=True)
            sample_path = samples_dir / "11Labs.mp3.wav"
            sample_path.write_bytes(b"RIFFnew-data")

            remote_sample = {
                "sample_id": "sample_existing",
                "file_name": "11Labs.mp3.wav",
                "hash": "different-remote-hash",
                "remove_background_noise": False,
                "trim_start": None,
                "trim_end": None,
            }

            with mock.patch.object(self.mod, "load_env_file_if_present"), mock.patch.object(
                self.mod, "_ensure_api_key", return_value="test-key"
            ), mock.patch.object(
                self.mod,
                "fetch_voice",
                return_value={"voice_id": "dPrTCMw2R7HQlznlgwCO", "samples": [remote_sample]},
            ):
                code, stdout, stderr = self._run_main(
                    [
                        "--config",
                        str(CONFIG_PATH),
                        "sync-samples",
                        "--voice",
                        "mike",
                        "--samples-dir",
                        str(samples_dir),
                        "--dry-run",
                    ]
                )

            self.assertEqual(code, 0)
            self.assertIn("Matched by filename: 1", stdout)
            self.assertIn("using filename fallback", stdout)

    def test_train_all_missing_only_starts_untrained_target_models(self):
        voice_payload = {
            "voice_id": "dPrTCMw2R7HQlznlgwCO",
            "fine_tuning": {
                "state": {
                    "eleven_multilingual_v2": "fine_tuned",
                    "eleven_multilingual_sts_v2": "not_started",
                }
            },
            "samples": [],
        }

        with mock.patch.object(self.mod, "load_env_file_if_present"), mock.patch.object(
            self.mod, "_ensure_api_key", return_value="test-key"
        ), mock.patch.object(self.mod, "fetch_voice", return_value=voice_payload), mock.patch.object(
            self.mod, "train_voice", return_value={}
        ) as train_mock:
            code, stdout, stderr = self._run_main(
                [
                    "--config",
                    str(CONFIG_PATH),
                    "train",
                    "--voice",
                    "mike",
                    "--all-missing",
                ]
            )

        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        train_mock.assert_called_once_with(
            voice_id="dPrTCMw2R7HQlznlgwCO",
            model_id="eleven_multilingual_sts_v2",
            api_key="test-key",
        )
        self.assertIn("eleven_multilingual_sts_v2", stdout)


if __name__ == "__main__":
    unittest.main()
