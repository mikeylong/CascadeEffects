from __future__ import annotations

import unittest
from pathlib import Path

from fluxlab.config import load_runtime
from fluxlab.io import read_json
from fluxlab.manifests import STAGE_DEFAULTS, load_prompt_canon, load_scene, validate_scene
from fluxlab.prompts import compile_negative_prompt, compile_positive_prompt
from fluxlab.workflows import OFFICIAL_GUIDANCE, OFFICIAL_SAMPLER, OFFICIAL_STEPS, load_api_template, patch_api_workflow


REPO_ROOT = Path(__file__).resolve().parents[1]


class ManifestContractTests(unittest.TestCase):
    def test_prompt_canon_loads(self) -> None:
        canon = load_prompt_canon(REPO_ROOT / "prompts" / "canon.json")
        self.assertIn("challenger", canon["subjects"])
        self.assertIn("shared_positive_style_prompt", canon)

    def test_scene_manifests_validate(self) -> None:
        for scene_path in sorted((REPO_ROOT / "scenes").glob("*.json")):
            scene = load_scene(scene_path)
            self.assertEqual(scene["stage_defaults"], STAGE_DEFAULTS)

    def test_manifest_rejects_wrong_stage_size(self) -> None:
        scene = read_json(REPO_ROOT / "scenes" / "challenger_a.json")
        scene["stage_defaults"]["lookdev"]["width"] = 999
        with self.assertRaisesRegex(ValueError, "stage_defaults.lookdev"):
            validate_scene(scene)


class PromptContractTests(unittest.TestCase):
    def test_positive_prompt_keeps_style_first(self) -> None:
        scene = load_scene(REPO_ROOT / "scenes" / "therac25_a.json")
        positive = compile_positive_prompt(scene)
        self.assertTrue(positive.startswith(scene["positive_style_prompt"]))
        self.assertIn(scene["subject_prompt"], positive)

    def test_negative_prompt_unchanged(self) -> None:
        scene = load_scene(REPO_ROOT / "scenes" / "boeing737max_b.json")
        self.assertEqual(compile_negative_prompt(scene), scene["negative_prompt"])

    def test_api_patch_only_touches_allowed_fields(self) -> None:
        template = load_api_template(REPO_ROOT / "templates" / "api" / "flux2_dev_text_to_image.api.json")
        model_filenames = {
            "text_encoder": "mistral_3_small_flux2_bf16.safetensors",
            "diffusion_model": "flux2-dev.safetensors",
            "vae": "flux2-vae.safetensors",
        }
        patched = patch_api_workflow(
            template,
            model_filenames=model_filenames,
            positive_prompt="positive",
            negative_prompt="negative",
            width=864,
            height=1536,
            batch_size=4,
            seed=4242,
            filename_prefix="cascadeeffects_fluxlab/test",
        )
        self.assertEqual(patched["prompt"]["1"]["inputs"]["unet_name"], model_filenames["diffusion_model"])
        self.assertEqual(patched["prompt"]["2"]["inputs"]["clip_name"], model_filenames["text_encoder"])
        self.assertEqual(patched["prompt"]["3"]["inputs"]["text"], "positive")
        self.assertEqual(patched["prompt"]["4"]["inputs"]["text"], "negative")
        self.assertEqual(patched["prompt"]["8"]["inputs"]["vae_name"], model_filenames["vae"])
        self.assertEqual(patched["prompt"]["9"]["inputs"]["width"], 864)
        self.assertEqual(patched["prompt"]["9"]["inputs"]["height"], 1536)
        self.assertEqual(patched["prompt"]["10"]["inputs"]["batch_size"], 4)
        self.assertEqual(patched["prompt"]["11"]["inputs"]["noise_seed"], 4242)
        self.assertEqual(patched["prompt"]["14"]["inputs"]["filename_prefix"], "cascadeeffects_fluxlab/test")
        self.assertEqual(patched["prompt"]["5"]["inputs"]["guidance"], OFFICIAL_GUIDANCE)
        self.assertEqual(patched["prompt"]["7"]["inputs"]["sampler_name"], OFFICIAL_SAMPLER)
        self.assertEqual(patched["prompt"]["9"]["inputs"]["steps"], OFFICIAL_STEPS)

    def test_runtime_points_to_expected_templates(self) -> None:
        runtime = load_runtime(REPO_ROOT)
        self.assertTrue(runtime.raw_template_path.exists())
        self.assertTrue(runtime.api_template_path.exists())


if __name__ == "__main__":
    unittest.main()
