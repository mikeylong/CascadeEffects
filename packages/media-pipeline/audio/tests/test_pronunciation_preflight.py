from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path("/Users/mike/CascadeEffects/packages/media-pipeline/audio")
HELPER_PATH = REPO_ROOT / "scripts" / "pronunciation_preflight.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PronunciationPreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module("pronunciation_preflight_under_test", HELPER_PATH)

    def test_default_lexicon_loads_known_rules(self):
        rules = self.mod.load_rules()
        rule_ids = {rule.id for rule in rules}
        self.assertIn("live_load_long_i", rule_ids)
        self.assertIn("duplicate_safety_verb", rule_ids)
        self.assertIn("wind_tunnel_hyphen_air_noun", rule_ids)

    def test_apply_rules_keeps_non_risk_wind_context_unchanged(self):
        transformed, applied = self.mod.apply_rules_to_text("The wind revealed the design weakness.")
        self.assertEqual(transformed, "The wind revealed the design weakness.")
        self.assertEqual(applied, [])

    def test_apply_rules_handles_seeded_pronunciation_risks(self):
        text = (
            "The dead load and live load changed. "
            "Why duplicate safety with expensive hardware? "
            "The wind-tunnel test mattered."
        )

        transformed, applied = self.mod.apply_rules_to_text(text)

        self.assertIn("lyve load", transformed)
        self.assertIn("dupli-kate safety", transformed)
        self.assertIn("wind tunnel test", transformed)
        self.assertNotIn("wind-tunnel", transformed)
        applied_ids = {item["rule_id"] for item in applied}
        self.assertIn("live_load_long_i", applied_ids)
        self.assertIn("duplicate_safety_verb", applied_ids)
        self.assertIn("wind_tunnel_hyphen_air_noun", applied_ids)

    def test_verify_compiled_fails_when_required_rule_metadata_is_missing(self):
        jobs = [
            {
                "out": "chunk_01.wav",
                "input": "The dead load and live load changed.",
                "spoken_input": "The dead load and live load changed.",
                "elevenlabs_text": "The dead load and live load changed.",
            }
        ]

        report = self.mod.verify_compiled_jobs(jobs)

        self.assertTrue(report["blockers"])
        self.assertEqual(report["blockers"][0]["missing_required_rule_ids"], ["live_load_long_i"])

    def test_cli_scan_reports_matches_without_blocking_approved_rules(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "jobs.jsonl"
            manifest.write_text(
                json.dumps({"out": "chunk_01.wav", "input": "The wind-tunnel test mattered."}) + "\n",
                encoding="utf-8",
            )

            report = self.mod.scan_jobs(self.mod.read_jsonl(manifest), text_key="input")

            self.assertEqual(report["blockers"], [])
            self.assertEqual(report["matched_job_count"], 1)


if __name__ == "__main__":
    unittest.main()
