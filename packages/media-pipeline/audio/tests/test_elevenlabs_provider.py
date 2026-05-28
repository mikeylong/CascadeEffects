import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path("/Users/mike/CascadeEffects/packages/media-pipeline/audio")
HELPER_PATH = REPO_ROOT / "scripts" / "elevenlabs_provider.py"
PROSODY_GUARD_PATH = REPO_ROOT / "scripts" / "prosody_guard.py"
CHALLENGER_SCRIPT = Path("/Users/mike/CascadeEffects/archive/season-01-reference/original-episodes/Ep1_Challenger/Ep1_Challenger.txt")
CHALLENGER_MANIFEST = REPO_ROOT / "tmp" / "ep1_challenger_production" / "final_jobs.jsonl"
CONFIGURED_V2_MODEL = "test_model_v2_hq"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def parse_json_blobs(raw: str) -> list[dict]:
    decoder = json.JSONDecoder()
    position = 0
    payloads = []
    while position < len(raw):
        brace = raw.find("{", position)
        if brace == -1:
            break
        payload, end = decoder.raw_decode(raw, brace)
        payloads.append(payload)
        position = end
    return payloads


class ElevenLabsProviderUnitTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module("elevenlabs_provider", HELPER_PATH)
        cls.guard_mod = load_module("prosody_guard_for_el_tests", PROSODY_GUARD_PATH)

    def _source_paragraph(self, tag: str, text: str):
        return self.mod.SourceParagraph(
            tag=tag,
            text=text,
            normalized=self.mod._normalize_alignment_text(text),
        )

    def test_tag_translation_matches_v3_strategy(self):
        calm_render, calm_spoken = self.mod.compile_tagged_paragraph(
            self._source_paragraph("calm", "The tone resets here."),
            previous_tag="frustrated",
            is_first_in_chunk=False,
            use_inline_tags=True,
        )
        deliberate_render, deliberate_spoken = self.mod.compile_tagged_paragraph(
            self._source_paragraph("deliberate", "Proceed with care."),
            previous_tag=None,
            is_first_in_chunk=False,
            use_inline_tags=True,
        )
        matter_render, matter_spoken = self.mod.compile_tagged_paragraph(
            self._source_paragraph("matter-of-fact", "The memo was direct."),
            previous_tag=None,
            is_first_in_chunk=False,
            use_inline_tags=True,
        )
        pauses_render, pauses_spoken = self.mod.compile_tagged_paragraph(
            self._source_paragraph("pauses", "One sentence. Another sentence."),
            previous_tag=None,
            is_first_in_chunk=False,
            use_inline_tags=True,
        )

        self.assertEqual(calm_spoken, "The tone resets here.")
        self.assertEqual(calm_render, "[calm] The tone resets here.")
        self.assertEqual(deliberate_render, "Proceed with care.")
        self.assertEqual(deliberate_spoken, "Proceed with care.")
        self.assertEqual(matter_render, "The memo was direct.")
        self.assertEqual(matter_spoken, "The memo was direct.")
        self.assertIn("[pause]", pauses_render)
        self.assertNotIn("<break", pauses_render)
        self.assertEqual(pauses_spoken, "One sentence. Another sentence.")

    def test_normalize_spoken_text_handles_decimals_clock_times_and_degrees(self):
        normalized = self.mod.normalize_spoken_text(
            "Launch at 11:38 a.m. The pad was 36°F. O-ring erosion reached 0.053 inches."
        )
        self.assertIn("11:38 AM", normalized)
        self.assertIn("36 degrees Fahrenheit", normalized)
        self.assertIn("zero point zero five three", normalized)

    @unittest.skipUnless(CHALLENGER_SCRIPT.exists(), "Challenger source script is required")
    @unittest.skipUnless(CHALLENGER_MANIFEST.exists(), "Challenger final manifest is required")
    def test_compile_manifest_aligns_challenger_and_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            output_one = tmp_path / "compiled_one.jsonl"
            output_two = tmp_path / "compiled_two.jsonl"
            jobs_one = self.mod.compile_manifest(
                jobs_path=CHALLENGER_MANIFEST,
                output_path=output_one,
                script_path=CHALLENGER_SCRIPT,
                strict_source_alignment=True,
                model_id="eleven_v3",
                continuity_chars=400,
            )
            jobs_two = self.mod.compile_manifest(
                jobs_path=CHALLENGER_MANIFEST,
                output_path=output_two,
                script_path=CHALLENGER_SCRIPT,
                strict_source_alignment=True,
                model_id="eleven_v3",
                continuity_chars=400,
            )

            self.assertEqual(jobs_one, jobs_two)
            self.assertTrue(jobs_one)
            for job in jobs_one:
                self.assertIn("spoken_input", job)
                self.assertIn("elevenlabs_text", job)
                self.assertIn("elevenlabs_seed", job)
                self.assertIn("elevenlabs_model_id", job)
                self.assertIn("elevenlabs_apply_text_normalization", job)
                self.assertIn("elevenlabs_voice_settings", job)
                self.assertLessEqual(len(job["elevenlabs_text"]), self.mod.MAX_COMPILED_CHARS)
            chunk_three = next(job for job in jobs_one if job["out"] == "ep1_challenger_chunk_03.wav")
            chunk_four = next(job for job in jobs_one if job["out"] == "ep1_challenger_chunk_04.wav")
            self.assertIn("zero point zero five three inches", chunk_three["spoken_input"])
            self.assertIn("11:38 AM Eastern", chunk_four["spoken_input"])
            self.assertNotIn("elevenlabs_previous_text", chunk_four)
            self.assertNotIn("elevenlabs_next_text", chunk_four)

    def test_compile_manifest_omits_continuity_when_disabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            manifest_path = tmp_path / "jobs.jsonl"
            output_path = tmp_path / "compiled.jsonl"
            manifest_path.write_text(
                "\n".join(
                    [
                        json.dumps({"out": "chunk_01.wav", "input": "First chunk."}),
                        json.dumps({"out": "chunk_02.wav", "input": "Second chunk."}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            jobs = self.mod.compile_manifest(
                jobs_path=manifest_path,
                output_path=output_path,
                script_path=None,
                strict_source_alignment=False,
                model_id=CONFIGURED_V2_MODEL,
                continuity_chars=0,
            )

            self.assertEqual(len(jobs), 2)
            for job in jobs:
                self.assertNotIn("elevenlabs_previous_text", job)
                self.assertNotIn("elevenlabs_next_text", job)

    def test_compile_manifest_non_v3_uses_spoken_text_without_inline_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            manifest_path = tmp_path / "jobs.jsonl"
            script_path = tmp_path / "script.txt"
            output_path = tmp_path / "compiled.jsonl"
            manifest_path.write_text(json.dumps({"out": "chunk_01.wav", "input": "The warning became ordinary."}) + "\n", encoding="utf-8")
            script_path.write_text("[resigned] The warning became ordinary.\n", encoding="utf-8")

            jobs = self.mod.compile_manifest(
                jobs_path=manifest_path,
                output_path=output_path,
                script_path=script_path,
                strict_source_alignment=True,
                model_id=CONFIGURED_V2_MODEL,
                continuity_chars=400,
            )

            self.assertEqual(len(jobs), 1)
            self.assertEqual(jobs[0]["spoken_input"], "The warning became ordinary.")
            self.assertEqual(jobs[0]["elevenlabs_text"], "The warning became ordinary.")

    def test_compile_manifest_applies_pronunciation_aliases_to_render_text_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            manifest_path = tmp_path / "jobs.jsonl"
            output_path = tmp_path / "compiled.jsonl"
            manifest_path.write_text(
                "\n".join(
                    [
                        json.dumps({"out": "chunk_01.wav", "input": "The dead load and live load changed."}),
                        json.dumps({"out": "chunk_02.wav", "input": "Why duplicate safety with expensive hardware?"}),
                        json.dumps({"out": "chunk_03.wav", "input": "The wind-tunnel model testing changed the field."}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            jobs = self.mod.compile_manifest(
                jobs_path=manifest_path,
                output_path=output_path,
                script_path=None,
                strict_source_alignment=False,
                model_id=CONFIGURED_V2_MODEL,
                continuity_chars=0,
            )

            self.assertEqual(jobs[0]["spoken_input"], "The dead load and live load changed.")
            self.assertEqual(jobs[0]["elevenlabs_text"], "The dead load and lyve load changed.")
            self.assertEqual(jobs[1]["spoken_input"], "Why duplicate safety with expensive hardware?")
            self.assertEqual(jobs[1]["elevenlabs_text"], "Why dupli-kate safety with expensive hardware?")
            self.assertEqual(jobs[2]["spoken_input"], "The wind-tunnel model testing changed the field.")
            self.assertEqual(jobs[2]["elevenlabs_text"], "The wind tunnel model testing changed the field.")
            self.assertIn("elevenlabs_pronunciation_lexicon_sha256", jobs[0])
            applied_ids = {
                item["rule_id"]
                for job in jobs
                for item in job["elevenlabs_pronunciation_applied_rules"]
            }
            self.assertIn("live_load_long_i", applied_ids)
            self.assertIn("duplicate_safety_verb", applied_ids)
            self.assertIn("wind_tunnel_hyphen_air_noun", applied_ids)

    def test_render_batch_dry_run_uses_provider_specific_payload_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            manifest_path = tmp_path / "compiled.jsonl"
            manifest_path.write_text(
                json.dumps(
                    {
                        "input": "The visible script text.",
                        "out": "chunk_01.wav",
                        "elevenlabs_text": "The spoken script text.",
                        "spoken_input": "The spoken script text.",
                        "elevenlabs_seed": 12345,
                        "elevenlabs_model_id": CONFIGURED_V2_MODEL,
                        "elevenlabs_apply_text_normalization": "on",
                        "elevenlabs_voice_settings": {
                            "stability": 0.6,
                            "similarity_boost": 0.8,
                            "style": 0.0,
                            "use_speaker_boost": True,
                            "speed": 1.0,
                        },
                        "elevenlabs_previous_text": "Previous context.",
                        "elevenlabs_next_text": "Next context.",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            proc = subprocess.run(
                [
                    "python3",
                    str(HELPER_PATH),
                    "render-batch",
                    "--input",
                    str(manifest_path),
                    "--out-dir",
                    str(tmp_path / "out"),
                    "--model",
                    CONFIGURED_V2_MODEL,
                    "--voice-id",
                    "voice_test_123",
                    "--output-format",
                    "wav_44100",
                    "--dry-run",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            payloads = parse_json_blobs(proc.stdout)
            self.assertEqual(len(payloads), 1)
            payload = payloads[0]
            self.assertLessEqual(
                set(payload),
                {
                    "text",
                    "model_id",
                    "apply_text_normalization",
                    "seed",
                    "voice_settings",
                    "previous_text",
                    "next_text",
                },
            )
            for forbidden in ("instructions", "voice", "input", "response_format", "stream_format"):
                self.assertNotIn(forbidden, payload)
            self.assertIn("Would write", proc.stdout)

    def test_render_batch_dry_run_includes_dictionary_locators_when_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            manifest_path = tmp_path / "compiled.jsonl"
            manifest_path.write_text(
                json.dumps(
                    {
                        "input": "The visible script text.",
                        "out": "chunk_01.wav",
                        "elevenlabs_text": "The spoken script text.",
                        "spoken_input": "The spoken script text.",
                        "elevenlabs_seed": 12345,
                        "elevenlabs_model_id": CONFIGURED_V2_MODEL,
                        "elevenlabs_apply_text_normalization": "on",
                        "elevenlabs_pronunciation_dictionary_locators": [
                            {"pronunciation_dictionary_id": "dict_123", "version_id": "ver_456"}
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            proc = subprocess.run(
                [
                    "python3",
                    str(HELPER_PATH),
                    "render-batch",
                    "--input",
                    str(manifest_path),
                    "--out-dir",
                    str(tmp_path / "out"),
                    "--model",
                    CONFIGURED_V2_MODEL,
                    "--voice-id",
                    "voice_test_123",
                    "--output-format",
                    "wav_44100",
                    "--dry-run",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            payload = parse_json_blobs(proc.stdout)[0]
            self.assertEqual(
                payload["pronunciation_dictionary_locators"],
                [{"pronunciation_dictionary_id": "dict_123", "version_id": "ver_456"}],
            )

    def test_render_batch_uses_env_default_model_when_flag_is_omitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            manifest_path = tmp_path / "compiled.jsonl"
            manifest_path.write_text(
                json.dumps(
                    {
                        "input": "The visible script text.",
                        "out": "chunk_01.wav",
                        "elevenlabs_text": "The spoken script text.",
                        "spoken_input": "The spoken script text.",
                        "elevenlabs_seed": 12345,
                        "elevenlabs_apply_text_normalization": "on",
                        "elevenlabs_voice_settings": {
                            "stability": 0.6,
                            "similarity_boost": 0.8,
                            "style": 0.0,
                            "use_speaker_boost": True,
                            "speed": 1.0,
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            with mock.patch.dict(os.environ, {"ELEVENLABS_DEFAULT_MODEL": CONFIGURED_V2_MODEL}, clear=False):
                proc = subprocess.run(
                    [
                        "python3",
                        str(HELPER_PATH),
                        "render-batch",
                        "--input",
                        str(manifest_path),
                        "--out-dir",
                        str(tmp_path / "out"),
                        "--voice-id",
                        "voice_test_123",
                        "--output-format",
                        "wav_44100",
                        "--dry-run",
                    ],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )

            payloads = parse_json_blobs(proc.stdout)
            self.assertEqual(len(payloads), 1)
            self.assertEqual(payloads[0]["model_id"], CONFIGURED_V2_MODEL)

    def test_render_batch_dry_run_omits_continuity_for_eleven_v3(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            manifest_path = tmp_path / "compiled.jsonl"
            manifest_path.write_text(
                json.dumps(
                    {
                        "input": "The visible script text.",
                        "out": "chunk_01.wav",
                        "elevenlabs_text": "[calm] The spoken script text.",
                        "spoken_input": "The spoken script text.",
                        "elevenlabs_seed": 12345,
                        "elevenlabs_model_id": "eleven_v3",
                        "elevenlabs_apply_text_normalization": "on",
                        "elevenlabs_voice_settings": {
                            "stability": 0.6,
                            "similarity_boost": 0.8,
                            "style": 0.0,
                            "use_speaker_boost": True,
                            "speed": 1.0,
                        },
                        "elevenlabs_previous_text": "Previous context.",
                        "elevenlabs_next_text": "Next context.",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            proc = subprocess.run(
                [
                    "python3",
                    str(HELPER_PATH),
                    "render-batch",
                    "--input",
                    str(manifest_path),
                    "--out-dir",
                    str(tmp_path / "out"),
                    "--model",
                    "eleven_v3",
                    "--voice-id",
                    "voice_test_123",
                    "--output-format",
                    "wav_44100",
                    "--dry-run",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            payloads = parse_json_blobs(proc.stdout)
            self.assertEqual(len(payloads), 1)
            payload = payloads[0]
            self.assertNotIn("previous_text", payload)
            self.assertNotIn("next_text", payload)

    def test_prosody_guard_rerender_uses_elevenlabs_helper(self):
        manifest_path = Path("/tmp/repair_jobs.jsonl")
        render_dir = Path("/tmp/rendered")
        helper_path = Path("/tmp/elevenlabs_provider.py")
        with mock.patch.dict(
            os.environ,
            {"ELEVEN_LABS_API_KEY": "test-key", "ELEVEN_LABS_VOICE_ID": "voice-id"},
            clear=False,
        ):
            with mock.patch.object(self.guard_mod.subprocess, "run") as run_mock:
                self.guard_mod.run_tts_batch(
                    manifest_path=manifest_path,
                    render_dir=render_dir,
                    provider="elevenlabs",
                    model=CONFIGURED_V2_MODEL,
                    voice="unused",
                    response_format="wav",
                    tts_gen=Path("/tmp/openai_tts.py"),
                    openai_python_spec="openai-spec",
                    elevenlabs_helper=helper_path,
                    elevenlabs_output_format="wav_44100",
                )

        run_mock.assert_called_once()
        cmd = run_mock.call_args.args[0]
        self.assertEqual(
            cmd,
            [
                "python3",
                str(helper_path),
                "render-batch",
                "--input",
                str(manifest_path),
                "--out-dir",
                str(render_dir),
                "--model",
                CONFIGURED_V2_MODEL,
                "--output-format",
                "wav_44100",
                "--force",
            ],
        )


if __name__ == "__main__":
    unittest.main()
