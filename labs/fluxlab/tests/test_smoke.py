from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from fluxlab.config import ensure_runtime_dirs, load_runtime
from fluxlab.io import read_json
from fluxlab.runs import build_bootstrap_report, export_scene_stage, refine_from_lookdev, render_scene


REPO_ROOT = Path(__file__).resolve().parents[1]


def _copy_tree(src: Path, dest: Path) -> None:
    shutil.copytree(src, dest, dirs_exist_ok=True)


class SmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix="fluxlab-smoke-")
        self.repo_root = Path(self.temp_dir.name) / "repo"
        self.comfy_root = Path(self.temp_dir.name) / "comfy"
        self.comfy_api_url = "http://127.0.0.1:8999"
        self.diffusion_filename = "flux2-dev-fp16.safetensors"
        self.repo_root.mkdir(parents=True, exist_ok=True)
        for name in ("bin", "config", "fluxlab", "prompts", "scenes", "scripts", "templates", "tests"):
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

    def test_bootstrap_reports_models_and_optional_server(self) -> None:
        report = build_bootstrap_report(self.runtime)
        self.assertTrue(report["ok"])
        self.assertFalse(report["server_reachable"])
        self.assertEqual(report["missing_models"], [])
        self.assertTrue(report["required_models"]["diffusion_model"].endswith(self.diffusion_filename))

    def test_export_render_and_refine_write_artifacts(self) -> None:
        exported = export_scene_stage(self.runtime, scene_id="challenger_a", stage="lookdev")
        self.assertEqual(exported["batch_size"], 4)
        self.assertEqual(exported["candidate_seeds"], [41001, 41002, 41003, 41004])
        self.assertTrue(Path(exported["ui_workflow_path"]).exists())
        self.assertTrue(Path(exported["api_workflow_path"]).exists())
        api_payload = read_json(Path(exported["api_workflow_path"]))
        self.assertEqual(api_payload["prompt"]["1"]["inputs"]["unet_name"], self.diffusion_filename)
        self.assertEqual(api_payload["meta"]["applied"]["model_filenames"]["diffusion_model"], self.diffusion_filename)

        rendered = render_scene(self.runtime, scene_id="challenger_a", stage="lookdev")
        self.assertTrue(Path(rendered["run_manifest_path"]).exists())
        run_payload = read_json(Path(rendered["run_manifest_path"]))
        self.assertEqual(run_payload["candidate_seeds"][2], 41003)

        refined = refine_from_lookdev(self.runtime, scene_id="challenger_a", run_id=rendered["run_id"], pick=2)
        self.assertEqual(refined["seed"], 41003)
        self.assertEqual((refined["width"], refined["height"], refined["batch_size"]), (1024, 1792, 1))

        scene_payload = read_json(self.repo_root / "scenes" / "challenger_a.json")
        self.assertEqual(scene_payload["selected_seed"], 41003)
        self.assertIn("refine", scene_payload["outputs"])

    def test_cli_bootstrap_exit_code(self) -> None:
        result = subprocess.run(
            [str(self.repo_root / "bin" / "ceflux"), "bootstrap"],
            capture_output=True,
            text=True,
            check=False,
            cwd=self.repo_root,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn('"ok": true', result.stdout)


if __name__ == "__main__":
    unittest.main()
