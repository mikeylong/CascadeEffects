from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from stylelab.evaluation import evaluate_still
from stylelab.io import read_json
from stylelab.manifests import load_profile


REPO_ROOT = Path(__file__).resolve().parents[1]


class EvaluationHardFailTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix="stylelab-eval-")
        self.temp_root = Path(self.temp_dir.name)
        self.profile = load_profile(REPO_ROOT / "profiles" / "minimal_surreal_editorial_v1.json")
        self.scene = read_json(REPO_ROOT / "scenes" / "scene_challenger_beat_07_thesis_close.json")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _image_path(self, name: str) -> Path:
        return self.temp_root / name

    def _blank_image(self) -> Image.Image:
        return Image.new("RGB", (1080, 1920), (238, 230, 216))

    def test_evaluator_flags_center_weighted_subject(self) -> None:
        image_path = self._image_path("center.png")
        self._blank_image().save(image_path)
        scene = dict(self.scene)
        scene["subject_anchor"] = dict(scene["subject_anchor"])
        scene["subject_anchor"]["placement"] = [0.5, 0.55]
        payload = evaluate_still(scene, image_path, self.profile)
        self.assertTrue(payload["hard_fail_checks"]["center_weighted_primary_subject"])

    def test_evaluator_flags_multiple_accents(self) -> None:
        image = self._blank_image()
        draw = ImageDraw.Draw(image)
        accent = self.profile["palette"]["accent"]
        draw.ellipse((180, 260, 260, 340), fill=accent)
        draw.ellipse((760, 440, 840, 520), fill=accent)
        image_path = self._image_path("accent.png")
        image.save(image_path)
        payload = evaluate_still(self.scene, image_path, self.profile)
        self.assertTrue(payload["hard_fail_checks"]["more_than_one_saturated_accent"])

    def test_evaluator_flags_detected_text(self) -> None:
        image = self._blank_image()
        draw = ImageDraw.Draw(image)
        for index in range(10):
            left = 120 + (index * 48)
            draw.rectangle((left, 200, left + 18, 226), fill=(10, 10, 10))
        image_path = self._image_path("text.png")
        image.save(image_path)
        payload = evaluate_still(self.scene, image_path, self.profile)
        self.assertTrue(payload["hard_fail_checks"]["detected_text"])

    def test_evaluator_flags_subtitle_zone_intrusion(self) -> None:
        image_path = self._image_path("subtitle.png")
        self._blank_image().save(image_path)
        scene = dict(self.scene)
        scene["subject_anchor"] = dict(scene["subject_anchor"])
        scene["subject_anchor"]["placement"] = [0.3, 0.82]
        payload = evaluate_still(scene, image_path, self.profile)
        self.assertTrue(payload["hard_fail_checks"]["subtitle_zone_intrusion"])


if __name__ == "__main__":
    unittest.main()
