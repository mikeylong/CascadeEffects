from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

try:
    from PIL import Image
except ModuleNotFoundError:  # pragma: no cover - dependency varies by environment
    Image = None


ROOT = Path("/Users/mike/CascadeEffects/packages/media-pipeline/viz")
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from midjourney_package_tool import (  # noqa: E402
    MidjourneyPackageAdapter,
    MidjourneyPackageError,
    MidjourneyPackageShot,
    build_reference_grid,
    load_midjourney_package_adapter,
    load_midjourney_package_shot,
)


class MidjourneyPackageToolTests(unittest.TestCase):
    def test_load_package_shots_cover_and_beat01(self) -> None:
        cover = load_midjourney_package_shot(
            "references/episodes/challenger/shorts/midjourney/challenger_short_minimal_surreal_v1/package.manifest.json",
            shot_id="cover",
            repo_root=ROOT,
        )
        beat_01 = load_midjourney_package_shot(
            "references/episodes/challenger/shorts/midjourney/challenger_short_minimal_surreal_v1/package.manifest.json",
            shot_id="beat_01",
            repo_root=ROOT,
        )

        self.assertEqual(cover.package_id, "challenger_short_minimal_surreal_v1__midjourney_v1")
        self.assertEqual(cover.shot_id, "cover")
        self.assertEqual(len(cover.reference_files), 4)
        self.assertEqual(beat_01.shot_id, "beat_01")
        self.assertEqual(len(beat_01.reference_files), 3)
        self.assertIn("ice on the pad", beat_01.prompt_text)

    def test_load_package_adapters_cover_and_beat01(self) -> None:
        package_manifest = (
            "references/episodes/challenger/shorts/midjourney/challenger_short_minimal_surreal_v1/package.manifest.json"
        )
        cover = load_midjourney_package_shot(package_manifest, shot_id="cover", repo_root=ROOT)
        beat_01 = load_midjourney_package_shot(package_manifest, shot_id="beat_01", repo_root=ROOT)
        cover_adapter = load_midjourney_package_adapter(
            "references/episodes/challenger/shorts/midjourney/challenger_short_minimal_surreal_v1/comfy_adapters/cover.json",
            shot=cover,
            repo_root=ROOT,
        )
        beat_adapter = load_midjourney_package_adapter(
            "references/episodes/challenger/shorts/midjourney/challenger_short_minimal_surreal_v1/comfy_adapters/beat_01.json",
            shot=beat_01,
            repo_root=ROOT,
        )

        self.assertEqual(cover_adapter.grid_layout_template, "cover_weighted_triptych")
        self.assertEqual(list(cover_adapter.included_reference_indices), [1, 3, 0])
        self.assertIn("no full shuttle vehicle", cover_adapter.negative_adapter_terms)
        self.assertEqual(cover_adapter.steer_target, "single_severe_warning_object")
        self.assertIn("compressed monolith silhouette", cover_adapter.steer_keep_traits)
        self.assertIn("compressed_monolith", cover_adapter.ranking_bias_tags)
        self.assertTrue(cover_adapter.draft_visual_softpass["enabled"])
        self.assertEqual(beat_adapter.grid_layout_template, "detail_left_bias_triptych")
        self.assertEqual(list(beat_adapter.included_reference_indices), [1, 0, 2])
        self.assertIn("favor icicle-heavy pipe detail", beat_adapter.prompt_adapter_append[0])
        self.assertEqual(beat_adapter.steer_target, "cold_pipe_winter_signal")
        self.assertIn("winter haze", beat_adapter.steer_keep_traits)
        self.assertIn("winter_haze", beat_adapter.ranking_bias_tags)

    def test_build_reference_grid_preserves_reference_order_for_three_refs(self) -> None:
        if Image is None:
            self.skipTest("Pillow is not available in this environment.")
        with tempfile.TemporaryDirectory(prefix="ce-midjourney-grid-") as temp_root:
            root = Path(temp_root)
            package_root = root / "package"
            package_root.mkdir(parents=True, exist_ok=True)
            colors = [(220, 30, 30, 255), (30, 180, 30, 255), (30, 30, 220, 255)]
            reference_files: list[str] = []
            for index, color in enumerate(colors, start=1):
                path = package_root / f"ref_{index}.png"
                Image.new("RGBA", (100, 100), color).save(path)
                reference_files.append(path.name)
            shot = MidjourneyPackageShot(
                package_manifest_path=package_root / "package.manifest.json",
                package_root=package_root,
                package_id="pkg",
                shot_id="beat_01",
                prompt_text="prompt",
                negative_terms=(),
                reference_files=tuple(reference_files),
                prompt_doc_path="prompt.txt",
                references_manifest_path="references.json",
            )
            output_path = root / "grid.png"
            build_reference_grid(shot, output_path=output_path, width=200, height=200)
            grid = Image.open(output_path).convert("RGBA")

            self.assertEqual(grid.getpixel((50, 50)), colors[0])
            self.assertEqual(grid.getpixel((150, 50)), colors[1])
            self.assertEqual(grid.getpixel((50, 150)), colors[2])
            self.assertEqual(grid.getpixel((150, 150)), (226, 228, 232, 255))

    def test_build_reference_grid_uses_adapter_crops_and_weighted_triptych(self) -> None:
        if Image is None:
            self.skipTest("Pillow is not available in this environment.")
        with tempfile.TemporaryDirectory(prefix="ce-midjourney-grid-") as temp_root:
            root = Path(temp_root)
            package_root = root / "package"
            package_root.mkdir(parents=True, exist_ok=True)

            def make_half_image(path: Path, left_color: tuple[int, int, int, int], right_color: tuple[int, int, int, int]) -> None:
                image = Image.new("RGBA", (100, 100), left_color)
                for x in range(50, 100):
                    for y in range(100):
                        image.putpixel((x, y), right_color)
                image.save(path)

            ref_paths = [package_root / f"ref_{index}.png" for index in range(4)]
            make_half_image(ref_paths[0], (255, 0, 0, 255), (0, 0, 255, 255))
            make_half_image(ref_paths[1], (0, 255, 0, 255), (255, 255, 0, 255))
            make_half_image(ref_paths[2], (255, 0, 255, 255), (0, 255, 255, 255))
            make_half_image(ref_paths[3], (120, 120, 120, 255), (240, 120, 120, 255))
            shot = MidjourneyPackageShot(
                package_manifest_path=package_root / "package.manifest.json",
                package_root=package_root,
                package_id="pkg",
                shot_id="cover",
                prompt_text="prompt",
                negative_terms=(),
                reference_files=tuple(path.name for path in ref_paths),
                prompt_doc_path="prompt.txt",
                references_manifest_path="references.json",
            )
            adapter = MidjourneyPackageAdapter(
                adapter_path=package_root / "adapter.json",
                shot_id="cover",
                included_reference_indices=(1, 3, 0),
                reference_crops={
                    1: (0.0, 0.0, 0.5, 1.0),
                    3: (0.5, 0.0, 1.0, 1.0),
                    0: (0.5, 0.0, 1.0, 1.0),
                },
                grid_layout_template="cover_weighted_triptych",
                prompt_adapter_append=("adapter clause",),
                negative_adapter_terms=("no example",),
                draft_visual_softpass={"enabled": True, "allowed_visual_failures": ["palette_discipline_below_threshold"]},
                steer_target="single_severe_warning_object",
                steer_keep_traits=("single-object severity",),
                steer_avoid_traits=("literal shuttle portrait",),
                ranking_bias_tags=("single_object_severity",),
            )
            output_path = root / "grid.png"
            manifest = build_reference_grid(shot, output_path=output_path, width=200, height=200, adapter=adapter)
            grid = Image.open(output_path).convert("RGBA")

            self.assertEqual(grid.getpixel((40, 100)), (0, 255, 0, 255))
            self.assertEqual(grid.getpixel((170, 40)), (240, 120, 120, 255))
            self.assertEqual(grid.getpixel((170, 160)), (0, 0, 255, 255))
            self.assertEqual(manifest["grid_layout"], "cover_weighted_triptych")
            self.assertEqual(manifest["adapter"]["included_reference_indices"], [1, 3, 0])
            self.assertEqual(manifest["adapter"]["steer_target"], "single_severe_warning_object")
            self.assertEqual(manifest["adapter"]["ranking_bias_tags"], ["single_object_severity"])

    def test_load_package_adapter_rejects_unknown_ranking_bias_tags(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-midjourney-package-") as temp_root:
            root = Path(temp_root)
            package_root = root / "package"
            package_root.mkdir(parents=True, exist_ok=True)
            for index in range(3):
                (package_root / f"ref_{index}.png").write_text("stub", encoding="utf-8")
            manifest_path = package_root / "package.manifest.json"
            manifest_path.write_text(
                """
                {
                  "package_id": "pkg",
                  "cover": {
                    "shot_id": "cover",
                    "prompt_text": "prompt",
                    "reference_files": ["ref_0.png", "ref_1.png", "ref_2.png"],
                    "negative_terms": []
                  },
                  "shots": []
                }
                """.strip()
                + "\n",
                encoding="utf-8",
            )
            shot = load_midjourney_package_shot(manifest_path, shot_id="cover", repo_root=ROOT)
            adapter_path = package_root / "adapter.json"
            adapter_path.write_text(
                """
                {
                  "shot_id": "cover",
                  "included_reference_indices": [0, 1, 2],
                  "reference_crops": {
                    "0": [0.0, 0.0, 1.0, 1.0],
                    "1": [0.0, 0.0, 1.0, 1.0],
                    "2": [0.0, 0.0, 1.0, 1.0]
                  },
                  "grid_layout_template": "cover_weighted_triptych",
                  "prompt_adapter_append": ["prompt"],
                  "negative_adapter_terms": ["full shuttle vehicle"],
                  "steer_target": "single_severe_warning_object",
                  "steer_keep_traits": ["single-object severity"],
                  "steer_avoid_traits": ["literal shuttle portrait"],
                  "ranking_bias_tags": ["unknown_tag"],
                  "draft_visual_softpass": {
                    "enabled": true,
                    "allowed_visual_failures": ["palette_discipline_below_threshold"]
                  }
                }
                """.strip()
                + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(MidjourneyPackageError) as exc:
                load_midjourney_package_adapter(adapter_path, shot=shot, repo_root=ROOT)
        self.assertIn("unsupported tags", str(exc.exception))

    def test_build_reference_grid_preserves_reference_order_for_four_refs(self) -> None:
        if Image is None:
            self.skipTest("Pillow is not available in this environment.")
        with tempfile.TemporaryDirectory(prefix="ce-midjourney-grid-") as temp_root:
            root = Path(temp_root)
            package_root = root / "package"
            package_root.mkdir(parents=True, exist_ok=True)
            colors = [
                (220, 30, 30, 255),
                (30, 180, 30, 255),
                (30, 30, 220, 255),
                (240, 180, 30, 255),
            ]
            reference_files: list[str] = []
            for index, color in enumerate(colors, start=1):
                path = package_root / f"ref_{index}.png"
                Image.new("RGBA", (100, 100), color).save(path)
                reference_files.append(path.name)
            shot = MidjourneyPackageShot(
                package_manifest_path=package_root / "package.manifest.json",
                package_root=package_root,
                package_id="pkg",
                shot_id="cover",
                prompt_text="prompt",
                negative_terms=(),
                reference_files=tuple(reference_files),
                prompt_doc_path="prompt.txt",
                references_manifest_path="references.json",
            )
            output_path = root / "grid.png"
            build_reference_grid(shot, output_path=output_path, width=200, height=200)
            grid = Image.open(output_path).convert("RGBA")

            self.assertEqual(grid.getpixel((50, 50)), colors[0])
            self.assertEqual(grid.getpixel((150, 50)), colors[1])
            self.assertEqual(grid.getpixel((50, 150)), colors[2])
            self.assertEqual(grid.getpixel((150, 150)), colors[3])

    def test_load_package_shot_fails_for_missing_manifest_shot_or_reference(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-midjourney-package-") as temp_root:
            root = Path(temp_root)
            with self.assertRaises(MidjourneyPackageError):
                load_midjourney_package_shot(root / "missing.manifest.json", shot_id="cover", repo_root=ROOT)

            package_root = root / "package"
            package_root.mkdir(parents=True, exist_ok=True)
            manifest_path = package_root / "package.manifest.json"
            manifest_path.write_text(
                """
                {
                  "package_id": "pkg",
                  "cover": {
                    "shot_id": "cover",
                    "prompt_text": "prompt",
                    "reference_files": ["missing.png"],
                    "negative_terms": []
                  },
                  "shots": []
                }
                """.strip()
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(MidjourneyPackageError) as missing_shot:
                load_midjourney_package_shot(manifest_path, shot_id="beat_01", repo_root=ROOT)
            self.assertIn("midjourney_shot_id", str(missing_shot.exception))

            with self.assertRaises(MidjourneyPackageError) as missing_reference:
                load_midjourney_package_shot(manifest_path, shot_id="cover", repo_root=ROOT)
            self.assertIn("reference file was not found", str(missing_reference.exception))


if __name__ == "__main__":
    unittest.main()
