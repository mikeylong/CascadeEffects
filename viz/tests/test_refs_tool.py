from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ModuleNotFoundError:  # pragma: no cover - dependency varies by environment
    Image = None
    ImageDraw = None


ROOT = Path("/Users/mike/Viz_CascadeEffects")
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from subject_reference_plate import (  # noqa: E402
    SubjectReferencePlateError,
    build_status_for_output,
    build_subject_reference_plate,
    build_subject_reference_plates_for_episode,
    load_plate_manifest,
)


@unittest.skipIf(Image is None, "Pillow is not available in this environment.")
class SubjectReferencePlateTests(unittest.TestCase):
    def make_episode_layout(self, root: Path) -> tuple[Path, Path, Path, Path]:
        references_root = root / "references"
        manifests_dir = references_root / "episodes" / "challenger" / "subject_reference_plates" / "manifests"
        generated_dir = references_root / "episodes" / "challenger" / "subject_reference_plates" / "generated"
        research_assets_dir = root / "Episodes_CascadeEffects" / "Ep1_Challenger" / "visual_research" / "research_assets"
        manifests_dir.mkdir(parents=True, exist_ok=True)
        generated_dir.mkdir(parents=True, exist_ok=True)
        research_assets_dir.mkdir(parents=True, exist_ok=True)
        return references_root, manifests_dir, generated_dir, research_assets_dir

    def write_source_inventory(self, research_assets_dir: Path, *, source_id: str, source_image_path: Path) -> None:
        inventory_path = research_assets_dir.parent / "source_inventory.json"
        inventory_payload = {
            "schema_version": 1,
            "sources": [
                {
                    "source_id": source_id,
                    "raw_asset_path": str(source_image_path.resolve()),
                    "candidate_label": "Synthetic source",
                    "candidate_role": "act_reference",
                }
            ],
        }
        inventory_path.write_text(json.dumps(inventory_payload, indent=2) + "\n", encoding="utf-8")

    def test_build_subject_reference_plate_outputs_portrait_png(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-plate-build-") as temp_root:
            root = Path(temp_root)
            references_root, manifests_dir, generated_dir, research_assets_dir = self.make_episode_layout(root)
            source_path = research_assets_dir / "act3_06.jpg"
            image = Image.new("RGB", (1200, 800), (232, 234, 238))
            draw = ImageDraw.Draw(image)
            draw.rectangle((120, 16, 1032, 760), fill=(48, 126, 196))
            draw.rectangle((180, 80, 470, 640), fill=(28, 34, 48))
            draw.rectangle((430, 320, 470, 420), fill=(228, 52, 52))
            image.save(source_path)
            self.write_source_inventory(research_assets_dir, source_id="act3_06", source_image_path=source_path)

            manifest_path = manifests_dir / "challenger_warning_cold.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "plate_id": "challenger_warning_cold",
                        "source_id": "act3_06",
                        "source_image_path": str(source_path),
                        "crop_box": [0.08, 0.02, 0.86, 0.95],
                        "subject_box": [0.18, 0.08, 0.56, 0.88],
                        "placement_box": [0.11, 0.13, 0.42, 0.61],
                        "canvas_size": [1024, 1792],
                        "background_mode": "neutral_matte",
                        "allow_humans": False,
                        "notes": "Synthetic cold-risk exterior plate.",
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            build_manifest = build_subject_reference_plate(manifest_path, output_path=generated_dir / "challenger_warning_cold.png")
            with Image.open(generated_dir / "challenger_warning_cold.png") as built_image:
                self.assertEqual(built_image.size, (1024, 1792))
                self.assertEqual(built_image.getpixel((40, 450)), (236, 236, 232))
                self.assertNotEqual(built_image.getpixel((210, 520)), (236, 236, 232))
            with Image.open(generated_dir / "challenger_warning_cold__vision.png") as vision_image:
                self.assertLess(vision_image.size[0], 1024)
                self.assertLess(vision_image.size[1], 1792)
                self.assertEqual(vision_image.mode, "RGBA")
            with Image.open(generated_dir / "challenger_warning_cold__layout.png") as layout_image:
                self.assertEqual(layout_image.size, (1024, 1792))
                self.assertEqual(layout_image.mode, "RGBA")
                alpha_extrema = layout_image.getchannel("A").getextrema()
                self.assertIsNotNone(alpha_extrema)
                self.assertLess(alpha_extrema[0], 255)
            with Image.open(generated_dir / "challenger_warning_cold__seed.png") as seed_image:
                self.assertEqual(seed_image.size, (1024, 1792))
                self.assertEqual(seed_image.mode, "RGBA")
                alpha_extrema = seed_image.getchannel("A").getextrema()
                self.assertIsNotNone(alpha_extrema)
                self.assertLess(alpha_extrema[0], 255)
            with Image.open(generated_dir / "challenger_warning_cold__mask.png") as mask_image:
                self.assertEqual(mask_image.size, (1024, 1792))
                self.assertEqual(mask_image.mode, "L")
            self.assertEqual(build_manifest["plate_id"], "challenger_warning_cold")
            self.assertEqual(build_manifest["preserved_crop_mode"], "subject_box_only")
            self.assertTrue(build_manifest["vision_ref_path"].endswith("__vision.png"))
            self.assertTrue(build_manifest["layout_mask_path"].endswith("__layout.png"))
            self.assertTrue(build_manifest["seed_rgba_path"].endswith("__seed.png"))
            self.assertTrue(build_manifest["soft_mask_path"].endswith("__mask.png"))
            self.assertFalse(build_manifest["palette_lock"]["active"])
            self.assertFalse(build_manifest["spatial_mask"]["active"])
            status = build_status_for_output(generated_dir / "challenger_warning_cold.png")
            assert status is not None
            self.assertTrue(status["ready"])
            self.assertTrue(status["vision_ref_path"].endswith("__vision.png"))
            self.assertTrue(status["layout_mask_path"].endswith("__layout.png"))
            self.assertTrue(status["seed_rgba_path"].endswith("__seed.png"))
            self.assertTrue(status["soft_mask_path"].endswith("__mask.png"))

            summary = build_subject_reference_plates_for_episode(references_root, "challenger")
            self.assertEqual(summary["plate_count"], 1)
            self.assertTrue((generated_dir / "subject_reference_plates.build.json").exists())

    def test_load_plate_manifest_rejects_invalid_boxes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-plate-boxes-") as temp_root:
            root = Path(temp_root)
            _references_root, manifests_dir, _generated_dir, research_assets_dir = self.make_episode_layout(root)
            source_path = research_assets_dir / "act4_03.jpg"
            Image.new("RGB", (1000, 800), (240, 240, 240)).save(source_path)
            self.write_source_inventory(research_assets_dir, source_id="act4_03", source_image_path=source_path)

            manifest_path = manifests_dir / "challenger_ignition_smoke.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "plate_id": "challenger_ignition_smoke",
                        "source_id": "act4_03",
                        "source_image_path": str(source_path),
                        "crop_box": [0.0, 0.0, 1.0, 1.0],
                        "subject_box": [0.2, 0.2, 0.2, 0.8],
                        "placement_box": [0.1, 0.13, 0.42, 0.61],
                        "canvas_size": [1024, 1792],
                        "background_mode": "neutral_matte",
                        "allow_humans": False,
                        "notes": "Bad box fixture.",
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(SubjectReferencePlateError) as exc:
                load_plate_manifest(manifest_path, episode_id="challenger")
            self.assertIn("positive-area box", str(exc.exception))

    def test_build_subject_reference_plate_palette_lock_neutralizes_non_accent_pixels(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-plate-palette-lock-") as temp_root:
            root = Path(temp_root)
            _references_root, manifests_dir, generated_dir, research_assets_dir = self.make_episode_layout(root)
            source_path = research_assets_dir / "opening_02.jpg"
            image = Image.new("RGB", (1200, 800), (236, 236, 232))
            draw = ImageDraw.Draw(image)
            draw.rectangle((220, 80, 520, 680), fill=(36, 82, 164))
            draw.rectangle((330, 170, 375, 460), fill=(252, 168, 24))
            image.save(source_path)
            self.write_source_inventory(research_assets_dir, source_id="opening_02", source_image_path=source_path)

            manifest_path = manifests_dir / "challenger_thesis_cover.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "plate_id": "challenger_thesis_cover",
                        "source_id": "opening_02",
                        "source_image_path": str(source_path),
                        "crop_box": [0.1, 0.05, 0.52, 0.92],
                        "subject_box": [0.12, 0.04, 0.82, 0.94],
                        "placement_box": [0.12, 0.14, 0.42, 0.58],
                        "accent_box": [0.19, 0.21, 0.23, 0.43],
                        "canvas_size": [1024, 1792],
                        "background_mode": "neutral_matte",
                        "allow_humans": False,
                        "notes": "Synthetic palette-lock cover fixture.",
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            build_manifest = build_subject_reference_plate(
                manifest_path,
                output_path=generated_dir / "challenger_thesis_cover.png",
            )
            with Image.open(generated_dir / "challenger_thesis_cover.png") as built_image:
                accent_pixel = built_image.getpixel((210, 500))
                neutralized_pixel = built_image.getpixel((150, 500))
                self.assertGreater(accent_pixel[0], accent_pixel[1])
                self.assertGreater(accent_pixel[0], accent_pixel[2])
                self.assertNotEqual(neutralized_pixel, (36, 82, 164))
                self.assertLess(abs(neutralized_pixel[0] - neutralized_pixel[1]), 40)
            self.assertTrue(build_manifest["palette_lock"]["active"])
            self.assertEqual(build_manifest["palette_lock"]["accent_box"], [0.19, 0.21, 0.23, 0.43])

    def test_build_subject_reference_plate_uses_cutout_source_without_context_leak(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-plate-cutout-") as temp_root:
            root = Path(temp_root)
            _references_root, manifests_dir, generated_dir, research_assets_dir = self.make_episode_layout(root)
            source_path = research_assets_dir / "opening_02.jpg"
            cutout_path = research_assets_dir / "opening_02_cutout.png"
            base = Image.new("RGB", (1200, 900), (232, 232, 228))
            draw = ImageDraw.Draw(base)
            draw.rectangle((0, 580, 1200, 900), fill=(86, 86, 86))
            draw.rectangle((120, 80, 520, 760), fill=(18, 38, 62))
            base.save(source_path)
            cutout = Image.new("RGBA", (500, 760), (0, 0, 0, 0))
            cutout_draw = ImageDraw.Draw(cutout)
            cutout_draw.rectangle((140, 40, 330, 720), fill=(230, 230, 234, 255))
            cutout_draw.rectangle((210, 80, 245, 430), fill=(210, 48, 46, 220))
            cutout.save(cutout_path)
            self.write_source_inventory(research_assets_dir, source_id="opening_02", source_image_path=source_path)

            manifest_path = manifests_dir / "challenger_thesis_cover.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "plate_id": "challenger_thesis_cover",
                        "source_id": "opening_02",
                        "source_image_path": str(source_path),
                        "source_cutout_path": str(cutout_path),
                        "crop_box": [0.1, 0.05, 0.9, 0.95],
                        "subject_box": [0.12, 0.05, 0.82, 0.95],
                        "placement_box": [0.12, 0.14, 0.42, 0.58],
                        "accent_box": [0.18, 0.19, 0.23, 0.43],
                        "canvas_size": [1024, 1792],
                        "background_mode": "neutral_matte_knockout",
                        "allow_humans": False,
                        "notes": "Synthetic cutout-driven cover fixture.",
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            build_manifest = build_subject_reference_plate(
                manifest_path,
                output_path=generated_dir / "challenger_thesis_cover.png",
            )
            with Image.open(generated_dir / "challenger_thesis_cover.png") as preview_image:
                roadway_pixel = preview_image.getpixel((150, 940))
                subject_pixel = preview_image.getpixel((214, 520))
                self.assertEqual(roadway_pixel, (236, 236, 232))
                self.assertNotEqual(subject_pixel, (236, 236, 232))
            self.assertEqual(build_manifest["preserved_crop_mode"], "source_cutout")

    def test_load_plate_manifest_rejects_invalid_generation_exclusion_box(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-plate-exclusion-box-") as temp_root:
            root = Path(temp_root)
            _references_root, manifests_dir, _generated_dir, research_assets_dir = self.make_episode_layout(root)
            source_path = research_assets_dir / "act3_06.jpg"
            Image.new("RGB", (1200, 800), (236, 236, 232)).save(source_path)
            self.write_source_inventory(research_assets_dir, source_id="act3_06", source_image_path=source_path)

            manifest_path = manifests_dir / "challenger_warning_cold.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "plate_id": "challenger_warning_cold",
                        "source_id": "act3_06",
                        "source_image_path": str(source_path),
                        "crop_box": [0.08, 0.02, 0.86, 0.95],
                        "subject_box": [0.18, 0.08, 0.56, 0.88],
                        "placement_box": [0.11, 0.13, 0.42, 0.61],
                        "generation_allow_box": [0.08, 0.12, 0.4, 0.58],
                        "generation_exclusion_boxes": [[0.0, 0.74, 1.2, 1.0]],
                        "canvas_size": [1024, 1792],
                        "background_mode": "neutral_matte",
                        "allow_humans": False,
                        "notes": "Bad exclusion box fixture.",
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(SubjectReferencePlateError) as exc:
                load_plate_manifest(manifest_path, episode_id="challenger")
            self.assertIn("generation_exclusion_boxes[0]", str(exc.exception))

    def test_load_plate_manifest_rejects_non_dominant_subject_box(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-plate-dominance-") as temp_root:
            root = Path(temp_root)
            _references_root, manifests_dir, _generated_dir, research_assets_dir = self.make_episode_layout(root)
            source_path = research_assets_dir / "act2_04.jpg"
            Image.new("RGB", (1280, 960), (240, 240, 240)).save(source_path)
            self.write_source_inventory(research_assets_dir, source_id="act2_04", source_image_path=source_path)

            manifest_path = manifests_dir / "challenger_warning_absorbed.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "plate_id": "challenger_warning_absorbed",
                        "source_id": "act2_04",
                        "source_image_path": str(source_path),
                        "crop_box": [0.0, 0.0, 1.0, 1.0],
                        "subject_box": [0.45, 0.45, 0.55, 0.55],
                        "placement_box": [0.18, 0.2, 0.68, 0.56],
                        "canvas_size": [1024, 1792],
                        "background_mode": "neutral_matte",
                        "allow_humans": False,
                        "notes": "Crowd-heavy fixture that should fail dominance validation.",
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(SubjectReferencePlateError) as exc:
                load_plate_manifest(manifest_path, episode_id="challenger")
            self.assertIn("dominant subject cluster", str(exc.exception))

    def test_build_status_detects_stale_source_after_retouch(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-plate-stale-") as temp_root:
            root = Path(temp_root)
            _references_root, manifests_dir, generated_dir, research_assets_dir = self.make_episode_layout(root)
            source_path = research_assets_dir / "opening_02.jpg"
            Image.new("RGB", (1920, 1536), (228, 228, 228)).save(source_path)
            self.write_source_inventory(research_assets_dir, source_id="opening_02", source_image_path=source_path)

            manifest_path = manifests_dir / "challenger_thesis_cover.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "plate_id": "challenger_thesis_cover",
                        "source_id": "opening_02",
                        "source_image_path": str(source_path),
                        "crop_box": [0.18, 0.02, 0.82, 0.92],
                        "subject_box": [0.26, 0.06, 0.7, 0.88],
                        "placement_box": [0.12, 0.13, 0.44, 0.63],
                        "canvas_size": [1024, 1792],
                        "background_mode": "neutral_matte",
                        "allow_humans": False,
                        "notes": "Synthetic cover fixture.",
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            build_subject_reference_plate(manifest_path, output_path=generated_dir / "challenger_thesis_cover.png")
            source_path.write_text("retouched", encoding="utf-8")
            status = build_status_for_output(generated_dir / "challenger_thesis_cover.png")
            assert status is not None
            self.assertFalse(status["ready"])
            self.assertIn("source image changed", status["reason"])
