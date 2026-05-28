import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path


REPO_ROOT = Path("/Users/mike/CascadeEffects/packages/media-pipeline/audio")
SCRIPT_PATH = REPO_ROOT / "scripts" / "sibilance_workflow.py"
TTS_SCRIPT_PATH = Path("/Users/mike/.codex/skills/speech/scripts/text_to_speech.py")
CHALLENGER_MASTER = Path("/Users/mike/CascadeEffects/archive/season-01-reference/original-episodes/Ep1_Challenger/final/Ep1_Challenger.wav")
CHALLENGER_MANIFEST = REPO_ROOT / "tmp/ep1_challenger_production/final_jobs.jsonl"
CHALLENGER_RENDER_DIR = REPO_ROOT / "tmp/ep1_challenger_production/rendered"
SEEDED_TIMES = [
    "00:31.147",
    "00:34.773",
    "02:26.773",
    "03:32.779",
    "06:46.059",
    "08:59.861",
    "10:09.323",
    "11:01.888",
    "12:45.995",
]
ANTI_SIBILANCE_SUFFIX = (
    "Consonants: keep S, SH, and CH soft and controlled; avoid sharp, bright, "
    "or hissy fricatives. Delivery: prefer rounded documentary diction over "
    "crisp edge; preserve clarity without exaggerated articulation."
)


def load_module():
    spec = importlib.util.spec_from_file_location("sibilance_workflow", SCRIPT_PATH)
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


@unittest.skipUnless(CHALLENGER_MASTER.exists(), "Challenger packaged master is required")
@unittest.skipUnless(CHALLENGER_MANIFEST.exists(), "Challenger final manifest is required")
@unittest.skipUnless(CHALLENGER_RENDER_DIR.exists(), "Challenger render dir is required")
class SibilanceWorkflowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module()

    def _write_report(self, directory: Path) -> Path:
        report = self.mod.analyze_master(
            CHALLENGER_MASTER,
            CHALLENGER_MANIFEST,
            CHALLENGER_RENDER_DIR,
            top_n=8,
        )
        report_path = directory / "report.json"
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return report_path

    def test_analyze_master_surfaces_chunk_04_as_worst_cluster(self):
        report = self.mod.analyze_master(
            CHALLENGER_MASTER,
            CHALLENGER_MANIFEST,
            CHALLENGER_RENDER_DIR,
            top_n=8,
        )
        first = report["hotspots"][0]
        self.assertEqual(first["chunk_id"], "ep1_challenger_chunk_04")
        self.assertEqual(first["hotspot_id"], "hotspot_01")
        self.assertGreater(first["score"], report["min_score"])
        self.assertGreaterEqual(first["master_time"], 0.0)
        self.assertGreaterEqual(first["chunk_local_time"], 0.0)
        self.assertLessEqual(first["chunk_local_time"], first["master_time"])
        self.assertGreaterEqual(first["score"], report["hotspots"][1]["score"])

    def test_first_pass_auditions_pair_cedar_and_marin_per_seed(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            report_path = self._write_report(tmp_path)
            output_path = tmp_path / "first_pass.jsonl"
            jobs = self.mod.build_audition_jobs(
                CHALLENGER_MANIFEST,
                CHALLENGER_RENDER_DIR,
                report_path=report_path,
                output_path=output_path,
                stage="first-pass",
                response_format="wav",
                top_n=8,
                seed_times=self.mod.parse_seed_times(SEEDED_TIMES),
                seed_tolerance=1.0,
                winner_voice=None,
                anti_sibilance_suffix=ANTI_SIBILANCE_SUFFIX,
            )
            self.assertEqual(len(jobs), 18)
            groups = defaultdict(list)
            for job in jobs:
                groups[job["source_hotspot_id"]].append(job)
            self.assertEqual(len(groups), len(SEEDED_TIMES))
            for group in groups.values():
                self.assertEqual(len(group), 2)
                self.assertEqual({job["voice"] for job in group}, {"cedar", "marin"})
                self.assertEqual({job["speed"] for job in group}, {0.95})
                self.assertEqual({job["input"] for job in group}.__len__(), 1)
                self.assertEqual({job["instructions"] for job in group}.__len__(), 1)

    def test_second_pass_auditions_keep_one_voice_and_add_suffix(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            report_path = self._write_report(tmp_path)
            output_path = tmp_path / "second_pass.jsonl"
            jobs = self.mod.build_audition_jobs(
                CHALLENGER_MANIFEST,
                CHALLENGER_RENDER_DIR,
                report_path=report_path,
                output_path=output_path,
                stage="second-pass",
                response_format="wav",
                top_n=8,
                seed_times=self.mod.parse_seed_times(["10:09.323"]),
                seed_tolerance=1.0,
                winner_voice="cedar",
                anti_sibilance_suffix=ANTI_SIBILANCE_SUFFIX,
            )
            self.assertEqual(len(jobs), 2)
            self.assertEqual({job["voice"] for job in jobs}, {"cedar"})
            self.assertEqual({job["speed"] for job in jobs}, {0.95, 0.93})
            for job in jobs:
                self.assertIn(ANTI_SIBILANCE_SUFFIX, job["instructions"])

    @unittest.skipUnless(TTS_SCRIPT_PATH.exists(), "Bundled TTS CLI is required")
    def test_dry_run_payload_only_uses_supported_offline_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            report_path = self._write_report(tmp_path)
            manifest_path = tmp_path / "payload_check.jsonl"
            self.mod.build_audition_jobs(
                CHALLENGER_MANIFEST,
                CHALLENGER_RENDER_DIR,
                report_path=report_path,
                output_path=manifest_path,
                stage="first-pass",
                response_format="wav",
                top_n=8,
                seed_times=self.mod.parse_seed_times(["10:09.323"]),
                seed_tolerance=1.0,
                winner_voice=None,
                anti_sibilance_suffix=ANTI_SIBILANCE_SUFFIX,
            )
            proc = subprocess.run(
                [
                    "python3",
                    str(TTS_SCRIPT_PATH),
                    "speak-batch",
                    "--input",
                    str(manifest_path),
                    "--out-dir",
                    str(tmp_path / "out"),
                    "--model",
                    "gpt-4o-mini-tts-2025-12-15",
                    "--response-format",
                    "wav",
                    "--dry-run",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            payloads = parse_json_blobs(proc.stdout)
            self.assertEqual(len(payloads), 2)
            allowed = {"model", "voice", "input", "response_format", "speed", "instructions"}
            for payload in payloads:
                self.assertLessEqual(set(payload), allowed)
                self.assertNotIn("stream_format", payload)


if __name__ == "__main__":
    unittest.main()
