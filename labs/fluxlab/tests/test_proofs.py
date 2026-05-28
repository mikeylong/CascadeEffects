from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from fluxlab.config import ensure_runtime_dirs, load_runtime
from fluxlab.io import read_json
from fluxlab.proofs import build_proof_report, export_proof_suite, load_proof_suite, render_proof_suite


REPO_ROOT = Path(__file__).resolve().parents[1]
SUITE_ID = "minimal_surreal_v3_first_look"


def _copy_tree(src: Path, dest: Path) -> None:
    shutil.copytree(src, dest, dirs_exist_ok=True)


class ProofContractTests(unittest.TestCase):
    def test_suite_loads_with_expected_shape(self) -> None:
        suite = load_proof_suite(REPO_ROOT / "proofs" / "suites" / f"{SUITE_ID}.json")
        self.assertEqual(len(suite["styles"]), 1)
        self.assertEqual(len(suite["cases"]), 2)
        self.assertEqual(suite["styles"][0]["id"], "minimal_surreal_editorial_v3")
        self.assertEqual(
            [case["id"] for case in suite["cases"]],
            ["single_object_or_device", "room_or_interior"],
        )
        self.assertEqual(
            suite["render_overrides"],
            {"width": 576, "height": 1024, "batch_size": 1, "steps": 12},
        )


class ProofSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix="fluxlab-proof-")
        self.repo_root = Path(self.temp_dir.name) / "repo"
        self.comfy_root = Path(self.temp_dir.name) / "comfy"
        self.comfy_api_url = "http://127.0.0.1:8999"
        self.diffusion_filename = "flux2-dev-fp16.safetensors"
        self.repo_root.mkdir(parents=True, exist_ok=True)
        for name in ("benchmarks", "bin", "config", "fluxlab", "proofs", "prompts", "scenes", "scripts", "templates", "tests"):
            src = REPO_ROOT / name
            dest = self.repo_root / name
            if src.is_dir():
                _copy_tree(src, dest)
            elif src.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
        (self.repo_root / "exports").mkdir(parents=True, exist_ok=True)
        (self.repo_root / "runs").mkdir(parents=True, exist_ok=True)
        for relative in (
            "models/text_encoders",
            "models/diffusion_models",
            "models/vae",
            "output",
            "user/default/workflows",
        ):
            (self.comfy_root / relative).mkdir(parents=True, exist_ok=True)
        (self.comfy_root / "models" / "text_encoders" / "mistral_3_small_flux2_bf16.safetensors").write_text("", encoding="utf-8")
        (self.comfy_root / "models" / "diffusion_models" / self.diffusion_filename).write_text("", encoding="utf-8")
        (self.comfy_root / "models" / "vae" / "flux2-vae.safetensors").write_text("", encoding="utf-8")
        (self.repo_root / "config" / "paths.env").write_text(
            (
                f"CE_COMFY_ROOT={self.comfy_root}\n"
                f"CE_COMFY_API_URL={self.comfy_api_url}\n"
                "CE_FLUXLAB_OUTPUT_NAMESPACE=cascadeeffects_fluxlab\n"
                f"CE_FLUXLAB_DIFFUSION_MODEL_FILENAME={self.diffusion_filename}\n"
            ),
            encoding="utf-8",
        )
        self.runtime = load_runtime(self.repo_root)
        ensure_runtime_dirs(self.runtime)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_filtered_proof_export_uses_overrides_and_is_isolated(self) -> None:
        before_scene = read_json(self.repo_root / "scenes" / "challenger_a.json")

        exported = export_proof_suite(
            self.runtime,
            suite_id=SUITE_ID,
            case_id="single_object_or_device",
        )

        self.assertEqual(exported["stage"], "proof")
        self.assertEqual(exported["render_overrides"], {"width": 576, "height": 1024, "batch_size": 1, "steps": 12})
        self.assertEqual(len(exported["jobs"]), 1)
        job = exported["jobs"][0]
        self.assertIn("/exports/proofs/", job["ui_workflow_path"])
        self.assertIn("/exports/proofs/", job["api_workflow_path"])
        self.assertIn("/runs/proofs/", exported["run_manifest_path"])
        self.assertEqual(job["candidate_seeds"], [51001])
        self.assertEqual(job["width"], 576)
        self.assertEqual(job["height"], 1024)
        self.assertEqual(job["batch_size"], 1)
        self.assertEqual(job["steps"], 12)

        api_payload = read_json(Path(job["api_workflow_path"]))
        self.assertEqual(api_payload["prompt"]["9"]["inputs"]["steps"], 12)
        self.assertEqual(api_payload["prompt"]["9"]["inputs"]["width"], 576)
        self.assertEqual(api_payload["prompt"]["9"]["inputs"]["height"], 1024)
        self.assertEqual(api_payload["prompt"]["10"]["inputs"]["batch_size"], 1)
        self.assertEqual(api_payload["meta"]["applied"]["steps"], 12)

        after_scene = read_json(self.repo_root / "scenes" / "challenger_a.json")
        self.assertEqual(before_scene, after_scene)

    def test_proof_render_and_report_do_not_touch_scenes(self) -> None:
        before_scene = read_json(self.repo_root / "scenes" / "therac25_a.json")

        rendered = render_proof_suite(
            self.runtime,
            suite_id=SUITE_ID,
            case_id="room_or_interior",
        )
        self.assertEqual(len(rendered["jobs"]), 1)
        self.assertIsNotNone(rendered["jobs"][0]["queue"])
        self.assertFalse(rendered["jobs"][0]["queue"]["queued"])

        report = build_proof_report(self.runtime, suite_id=SUITE_ID, run_id=rendered["run_id"])
        report_json = read_json(Path(report["report_json_path"]))
        self.assertEqual(report_json["stage"], "proof")
        self.assertEqual(len(report_json["cases"]), 1)
        self.assertEqual(report_json["cases"][0]["case_id"], "room_or_interior")
        self.assertNotIn("winner", report_json["cases"][0])
        self.assertNotIn("overall_summary", report_json)
        style_report = report_json["cases"][0]["styles"][0]
        self.assertEqual(style_report["style_id"], "minimal_surreal_editorial_v3")
        self.assertEqual(style_report["review"], {"notes": ""})
        self.assertEqual(style_report["steps"], 12)
        self.assertTrue(Path(report["report_markdown_path"]).exists())

        after_scene = read_json(self.repo_root / "scenes" / "therac25_a.json")
        self.assertEqual(before_scene, after_scene)


if __name__ == "__main__":
    unittest.main()
