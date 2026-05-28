from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from stylelab.io import read_json
from stylelab.manifests import (
    EXPECTED_FINAL_SIZE,
    load_profile,
    load_scene,
    load_short,
    normalize_final_size,
    validate_scene_manifest,
    validate_short_manifest,
)
from stylelab.prompts import compile_negative_prompt, compile_prompt, compile_style_profile, model_family_for_mode


REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_short_fixture(temp_root: Path, mutate=None) -> Path:
    audio_path = temp_root / "audio.wav"
    transcript_path = temp_root / "transcript.txt"
    short_path = temp_root / "challenger_short_v1.json"
    audio_path.write_bytes(b"fixture audio")
    transcript_path.write_text("Fixture transcript.", encoding="utf-8")
    short_manifest = read_json(REPO_ROOT / "shorts" / "challenger_short_v1.json")
    short_manifest["audio_path"] = str(audio_path)
    short_manifest["transcript_path"] = str(transcript_path)
    if mutate is not None:
        mutate(short_manifest)
    short_path.write_text(json.dumps(short_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return short_path


class ManifestContractTests(unittest.TestCase):
    def test_benchmark_scene_manifest_validates(self) -> None:
        scene = load_scene(REPO_ROOT / "scenes" / "scene_01_shuttle_exterior.json")
        self.assertEqual(scene["id"], "scene_01_shuttle_exterior")

    def test_short_manifest_validates(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stylelab-short-contract-") as temp_dir:
            short_manifest = load_short(_write_short_fixture(Path(temp_dir)), scenes_root=REPO_ROOT / "scenes")
            self.assertEqual(short_manifest["id"], "challenger_short_v1")

    def test_manifest_rejects_non_vertical_size(self) -> None:
        scene = read_json(REPO_ROOT / "scenes" / "scene_01_shuttle_exterior.json")
        scene["final_size"] = {"width": 1920, "height": 1080}
        with self.assertRaisesRegex(ValueError, "final_size"):
            validate_scene_manifest(scene)

    def test_manifest_rejects_missing_surreal_breach(self) -> None:
        scene = read_json(REPO_ROOT / "scenes" / "scene_challenger_beat_02_normalized_damage.json")
        del scene["surreal_breach"]
        with self.assertRaisesRegex(ValueError, "surreal_breach"):
            validate_scene_manifest(scene)

    def test_manifest_rejects_negative_prompt_override(self) -> None:
        scene = read_json(REPO_ROOT / "scenes" / "scene_02_control_room.json")
        scene["prompt_overrides"]["negative_prompt"] = "forbidden"
        with self.assertRaisesRegex(ValueError, "negative_prompt"):
            validate_scene_manifest(scene)

    def test_short_manifest_rejects_unknown_render_mode(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stylelab-short-contract-") as temp_dir:
            short_path = _write_short_fixture(
                Path(temp_dir),
                mutate=lambda short_manifest: short_manifest["beats"][0].__setitem__("render_as", "panorama"),
            )
            short_manifest = read_json(short_path)
            with self.assertRaisesRegex(ValueError, "render_as"):
                validate_short_manifest(short_manifest, scenes_root=REPO_ROOT / "scenes")

    def test_normalize_final_size_defaults_to_vertical_target(self) -> None:
        width, height = normalize_final_size({})
        self.assertEqual((width, height), (EXPECTED_FINAL_SIZE["width"], EXPECTED_FINAL_SIZE["height"]))


class PromptContractTests(unittest.TestCase):
    def test_style_profile_compiles_positive_canon(self) -> None:
        profile = load_profile(REPO_ROOT / "profiles" / "minimal_surreal_editorial_v1.json")
        compiled = compile_style_profile(profile)
        self.assertEqual(compiled["id"], "minimal_surreal_editorial_v1")
        self.assertIn("reduction", profile["rules"])
        self.assertIn("implied_story", profile["rules"])
        self.assertTrue(all("negative prompt" not in part.lower() for part in compiled["canon"]))
        self.assertIn("caption_safe_defaults", compiled)

    def test_prompt_builder_includes_scene_translation_and_model_contract(self) -> None:
        scene = load_scene(REPO_ROOT / "scenes" / "scene_challenger_beat_03_burden_shift.json")
        profile = load_profile(REPO_ROOT / "profiles" / "minimal_surreal_editorial_v1.json")
        prompt = compile_prompt(scene, profile, mode="final")
        negative_prompt = compile_negative_prompt(profile)
        self.assertIn("Hero subject:", prompt)
        self.assertIn("Subject archetype:", prompt)
        self.assertIn("Historical anchor:", prompt)
        self.assertIn("Single surreal breach:", prompt)
        self.assertIn("Caption safety:", prompt)
        self.assertIn("no source references are used", prompt)
        self.assertIn("text", negative_prompt)
        self.assertEqual(model_family_for_mode("final"), "flux2_dev_reference_contract")


if __name__ == "__main__":
    unittest.main()
