from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from fluxlab.benchmarks import build_benchmark_report, export_benchmark_suite, load_benchmark_suite, render_benchmark_suite
from fluxlab.config import ensure_runtime_dirs, load_runtime
from fluxlab.io import read_json
from fluxlab.manifests import ALLOWED_SCENE_IDS


REPO_ROOT = Path(__file__).resolve().parents[1]
SUITE_ID = "minimal_surreal_v1_v2_v3_go_no_go"


def _copy_tree(src: Path, dest: Path) -> None:
    shutil.copytree(src, dest, dirs_exist_ok=True)


class BenchmarkContractTests(unittest.TestCase):
    def test_suite_loads_with_expected_shape(self) -> None:
        suite = load_benchmark_suite(REPO_ROOT / "benchmarks" / "suites" / f"{SUITE_ID}.json")
        self.assertEqual(suite["stage"], "lookdev")
        self.assertEqual(len(suite["styles"]), 3)
        self.assertEqual(len(suite["cases"]), 8)
        self.assertEqual(
            [style["id"] for style in suite["styles"]],
            [
                "minimal_surreal_editorial_v1",
                "minimal_surreal_editorial_v2",
                "minimal_surreal_editorial_v3",
            ],
        )
        self.assertEqual(
            [case["id"] for case in suite["cases"]],
            [
                "single_object_or_device",
                "single_human_figure",
                "small_human_group",
                "room_or_interior",
                "structure_or_exterior",
                "vehicle_vessel_or_aircraft",
                "site_or_landscape",
                "fragment_or_detail",
            ],
        )


class BenchmarkSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix="fluxlab-bench-")
        self.repo_root = Path(self.temp_dir.name) / "repo"
        self.comfy_root = Path(self.temp_dir.name) / "comfy"
        self.comfy_api_url = "http://127.0.0.1:8999"
        self.diffusion_filename = "flux2-dev-fp16.safetensors"
        self.repo_root.mkdir(parents=True, exist_ok=True)
        for name in ("benchmarks", "bin", "config", "fluxlab", "prompts", "scenes", "scripts", "templates", "tests"):
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

    def test_filtered_benchmark_export_is_isolated(self) -> None:
        before_scene = read_json(self.repo_root / "scenes" / "challenger_a.json")
        self.assertNotIn("single_object_or_device", ALLOWED_SCENE_IDS)

        exported = export_benchmark_suite(
            self.runtime,
            suite_id=SUITE_ID,
            case_id="single_object_or_device",
            style_id="minimal_surreal_editorial_v3",
        )

        self.assertEqual(exported["stage"], "lookdev")
        self.assertEqual(len(exported["jobs"]), 1)
        job = exported["jobs"][0]
        self.assertIn("/exports/benchmarks/", job["ui_workflow_path"])
        self.assertIn("/exports/benchmarks/", job["api_workflow_path"])
        self.assertIn("/runs/benchmarks/", exported["run_manifest_path"])
        self.assertEqual(job["candidate_seeds"], [51001, 51002, 51003, 51004])
        self.assertTrue(Path(job["ui_workflow_path"]).exists())
        self.assertTrue(Path(job["api_workflow_path"]).exists())
        self.assertTrue(job["positive_prompt"].startswith(exported["styles"][0]["positive_style_prompt"]))
        self.assertIn(exported["cases"][0]["prompt_body"], job["positive_prompt"])

        after_scene = read_json(self.repo_root / "scenes" / "challenger_a.json")
        self.assertEqual(before_scene, after_scene)

    def test_benchmark_render_and_report_do_not_touch_scenes(self) -> None:
        before_scene = read_json(self.repo_root / "scenes" / "therac25_a.json")

        rendered = render_benchmark_suite(
            self.runtime,
            suite_id=SUITE_ID,
            case_id="fragment_or_detail",
            style_id="minimal_surreal_editorial_v2",
        )
        self.assertEqual(len(rendered["jobs"]), 1)
        self.assertIsNotNone(rendered["jobs"][0]["queue"])
        self.assertFalse(rendered["jobs"][0]["queue"]["queued"])

        report = build_benchmark_report(self.runtime, suite_id=SUITE_ID, run_id=rendered["run_id"])
        report_json = read_json(Path(report["report_json_path"]))
        self.assertEqual(len(report_json["cases"]), 1)
        self.assertEqual(report_json["cases"][0]["case_id"], "fragment_or_detail")
        self.assertEqual(report_json["cases"][0]["styles"][0]["style_id"], "minimal_surreal_editorial_v2")
        self.assertEqual(
            set(report_json["cases"][0]["styles"][0]["review"].keys()),
            {"subject_fidelity", "anomaly_clarity", "consistency", "notes"},
        )
        self.assertTrue(Path(report["report_markdown_path"]).exists())

        after_scene = read_json(self.repo_root / "scenes" / "therac25_a.json")
        self.assertEqual(before_scene, after_scene)


if __name__ == "__main__":
    unittest.main()
