from __future__ import annotations

import base64
import copy
import io
import json
import os
import sys
import tempfile
import unittest
import zipfile
from argparse import Namespace
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

try:
    from PIL import Image, ImageDraw, ImageStat
except ModuleNotFoundError:  # pragma: no cover - environment-specific skip
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]
    ImageStat = None  # type: ignore[assignment]


ROOT = Path("/Users/mike/CascadeEffects/packages/media-pipeline/viz")
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

if Image is not None:
    import workbench_tool as workbench_tool_module  # noqa: E402
    from workbench_tool import (  # noqa: E402
        PRESET_DEFAULTS,
        DEFAULT_PRESET_ID,
        DEFAULT_EFFECT_MODEL,
        MASK_STATUS_APPROVED,
        MASK_STATUS_REVIEW_REQUIRED,
        MODEL_SOURCE_STATUS_SELECTED,
        PRIOR_ASSIST_REASON_LOW_FIT,
        PRIOR_ASSIST_REASON_NOT_ELIGIBLE,
        PRIOR_ASSIST_STATUS_ACTIVE,
        PRIOR_ASSIST_STATUS_INACTIVE,
        PRIOR_ASSIST_STATUS_REJECTED,
        VOLUME_BACKEND_ACQUIRED_SHELL,
        VOLUME_BACKEND_MODEL_SOURCE,
        WorkbenchError,
        add_source_candidate,
        approve_project_look,
        animated_particle_position,
        apply_mask_brush,
        apply_project_preset,
        apply_project_patch,
        approve_mask,
        burn_project_video,
        build_effect_scene_payload,
        camera_vectors,
        build_export_request,
        clear_project_model_source,
        connect_sketchfab_token,
        export_project_shot,
        emitter_defaults,
        fetch_project_model_source,
        generate_active_particle_specs,
        generate_particle_specs,
        init_project_bundle,
        load_project,
        particle_motion_context,
        plume_emission_envelope,
        project_point,
        project_mask_paths,
        read_mask_file,
        reset_scene_to_preset_baseline,
        remove_source_candidate,
        render_preview_png,
        render_frame,
        resolve_sketchfab_access_token,
        resolve_preset_scene,
        save_project_preset,
        search_project_model_sources,
        sketchfab_auth_status,
        select_source_candidate,
        disconnect_sketchfab_auth,
        select_project_snapshot,
        select_project_model_source,
        upload_project_model_source,
    )
    from workbench_model_source import (  # noqa: E402
        PARTICLE_MOTION_ANCHOR_ATTACHMENT,
        PARTICLE_MOTION_ANCHOR_SHELL,
        PARTICLE_MOTION_EMISSION_PLUME,
        ModelSourceError,
        canonical_subject_view_vectors,
        external_model_source_resources,
        fetch_model_candidate,
        fetch_nasa,
        fetch_poly_pizza,
        fetch_sketchfab,
        infer_subject_frame_from_points,
        normalize_fetched_model_candidate,
        rotate_model_source_vector,
        search_model_candidates,
        search_poly_pizza,
        search_sketchfab,
    )


@unittest.skipIf(Image is None, "Pillow is required for workbench tool tests.")
class WorkbenchToolTests(unittest.TestCase):
    def _write_isolated_source_image(self, root: Path) -> Path:
        image_path = root / "subject.png"
        image = Image.new("RGBA", (640, 640), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image, "RGBA")
        draw.ellipse((238, 56, 476, 286), fill=(232, 232, 232, 255))
        draw.polygon(
            [
                (392, 136),
                (452, 172),
                (430, 220),
                (382, 210),
            ],
            fill=(220, 220, 220, 255),
        )
        draw.rounded_rectangle((276, 252, 374, 610), radius=32, fill=(198, 198, 198, 255))
        draw.ellipse((206, 112, 310, 246), fill=(184, 184, 184, 255))
        image.save(image_path)
        return image_path

    def _write_scenic_source_image(self, root: Path) -> Path:
        image_path = root / "scenic.jpg"
        image = Image.new("RGB", (960, 540), (226, 226, 226))
        draw = ImageDraw.Draw(image, "RGB")
        draw.rectangle((0, 0, 959, 220), fill=(165, 181, 214))
        draw.rectangle((0, 220, 959, 539), fill=(238, 235, 228))
        draw.rectangle((440, 140, 520, 420), fill=(58, 58, 58))
        draw.polygon([(430, 160), (530, 160), (480, 34)], fill=(82, 82, 82))
        draw.rectangle((388, 388, 572, 430), fill=(128, 112, 94))
        image.save(image_path, quality=95)
        return image_path

    def _write_shuttle_stack_source_image(self, root: Path) -> Path:
        image_path = root / "space_shuttle_stack.png"
        width, height = 640, 640
        image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image, "RGBA")

        def ellipse(cx: float, cy: float, rx: float, ry: float, fill: tuple[int, int, int, int]) -> None:
            px = (width * 0.5) + (cx * 240.0)
            py = 340.0 + (cy * 220.0)
            draw.ellipse((px - (rx * 240.0), py - (ry * 220.0), px + (rx * 240.0), py + (ry * 220.0)), fill=fill)

        ellipse(0.0, -0.04, 0.16, 0.92, (232, 232, 232, 255))
        ellipse(-0.24, -0.06, 0.082, 0.82, (214, 214, 214, 255))
        ellipse(0.24, -0.06, 0.082, 0.82, (214, 214, 214, 255))
        ellipse(0.15, 0.22, 0.22, 0.30, (196, 196, 196, 255))
        ellipse(0.12, 0.22, 0.30, 0.17, (208, 208, 208, 220))
        ellipse(0.0, -0.98, 0.10, 0.10, (240, 240, 240, 255))
        image.save(image_path)
        return image_path

    def _write_mask_image(self, root: Path) -> Path:
        mask_path = root / "mask.png"
        mask = Image.new("L", (960, 540), 0)
        draw = ImageDraw.Draw(mask)
        draw.rectangle((430, 28, 530, 430), fill=255)
        mask.save(mask_path)
        return mask_path

    def _proposal_mask(self, size: tuple[int, int]) -> Image.Image:
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rectangle((410, 30, 540, 430), fill=255)
        return mask

    def _write_cube_obj(self, root: Path) -> Path:
        obj_path = root / "cube.obj"
        obj_path.write_text(
            "\n".join(
                [
                    "v -1 -1 -1",
                    "v 1 -1 -1",
                    "v 1 1 -1",
                    "v -1 1 -1",
                    "v -1 -1 1",
                    "v 1 -1 1",
                    "v 1 1 1",
                    "v -1 1 1",
                    "f 1 2 3",
                    "f 1 3 4",
                    "f 5 6 7",
                    "f 5 7 8",
                    "f 1 5 8",
                    "f 1 8 4",
                    "f 2 6 7",
                    "f 2 7 3",
                    "f 4 3 7",
                    "f 4 7 8",
                    "f 1 2 6",
                    "f 1 6 5",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return obj_path

    def _write_wedge_obj(self, root: Path) -> Path:
        obj_path = root / "wedge.obj"
        obj_path.write_text(
            "\n".join(
                [
                    "v -2 -1 -1",
                    "v -2 1 -1",
                    "v -2 1 1",
                    "v -2 -1 1",
                    "v 2 -0.35 -0.35",
                    "v 2 0.35 -0.35",
                    "v 2 0.35 0.35",
                    "v 2 -0.35 0.35",
                    "f 1 2 6",
                    "f 1 6 5",
                    "f 2 3 7",
                    "f 2 7 6",
                    "f 3 4 8",
                    "f 3 8 7",
                    "f 4 1 5",
                    "f 4 5 8",
                    "f 1 4 3",
                    "f 1 3 2",
                    "f 5 6 7",
                    "f 5 7 8",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return obj_path

    def _init_args(
        self,
        root: Path,
        source_image: Path | None,
        *,
        mask_image: Path | None = None,
        behavior: str = "The subject dissolves into a monochrome particle trail.",
        preset: str = "default",
    ) -> Namespace:
        return Namespace(
            project=str(root / "workbench" / "project.json"),
            source_image=str(source_image) if source_image else None,
            mask_image=str(mask_image) if mask_image else None,
            episode_id="adhoc",
            motion_item_id="hero_subject_test",
            behavior=behavior,
            preset=preset,
            frames=33,
            width=640,
            height=384,
            fps=24,
            pipeline="particle_workbench",
            min_duration_seconds=5.0,
            seed=4242,
            force=False,
            command="init",
            repo_root=str(ROOT),
        )

    def _upload_payload(self, image_path: Path, *, label: str | None = None) -> dict[str, str]:
        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        suffix = image_path.suffix.lower()
        mime = "image/png" if suffix == ".png" else "image/jpeg"
        return {
            "filename": image_path.name,
            "label": label or image_path.stem.replace("_", " ").title(),
            "content_base64": f"data:{mime};base64,{encoded}",
        }

    def test_parse_args_init_defaults_to_uhd60(self) -> None:
        with mock.patch.object(
            sys,
            "argv",
            [
                "bin/ce workbench",
                "--repo-root",
                str(ROOT),
                "init",
                "--project",
                "/tmp/project.json",
                "--episode-id",
                "adhoc",
                "--motion-item-id",
                "hero_subject_test",
            ],
        ):
            args = workbench_tool_module.parse_args()

        self.assertEqual(args.width, workbench_tool_module.DEFAULT_WIDTH)
        self.assertEqual(args.height, workbench_tool_module.DEFAULT_HEIGHT)
        self.assertEqual(args.fps, workbench_tool_module.DEFAULT_FPS)
        self.assertEqual(args.preset, DEFAULT_PRESET_ID)

    def _model_upload_payload(self, model_path: Path, *, label: str | None = None) -> dict[str, str]:
        encoded = base64.b64encode(model_path.read_bytes()).decode("ascii")
        suffix = model_path.suffix.lower()
        mime = {
            ".obj": "text/plain",
            ".glb": "model/gltf-binary",
            ".gltf": "model/gltf+json",
        }.get(suffix, "application/octet-stream")
        return {
            "filename": model_path.name,
            "label": label or model_path.stem.replace("_", " ").title(),
            "content_base64": f"data:{mime};base64,{encoded}",
        }

    def _particles_for_project(self, project_path: Path) -> tuple[dict[str, object], list[dict[str, float]]]:
        project = load_project(project_path)
        with Image.open(project["source_image"]["path"]) as opened:
            source_image = opened.convert("RGBA")
            mask_image = read_mask_file(project_mask_paths(project_path, project["active_source_id"]).approved, source_image.size)
            particles = generate_particle_specs(
                scene=project["scene"],
                source_image=source_image,
                mask_image=mask_image,
                subject_analysis=project["subject_analysis"],
            )
        return project, particles

    def _active_particles_for_project(self, project_path: Path) -> tuple[dict[str, object], list[dict[str, float]]]:
        project = load_project(project_path)
        return project, generate_active_particle_specs(project_path, project)

    def _fake_export_session(self, captured: list[dict[str, object]] | None = None):
        @contextmanager
        def manager(project_path: Path, export_project: dict[str, object]):
            if captured is not None:
                captured.append(
                    {
                        "project_path": Path(project_path),
                        "project": copy.deepcopy(export_project),
                    }
                )
            yield "http://127.0.0.1:9999"

        return manager

    def _fake_webgl_export(self):
        def export(_repo_root: Path, _session_url: str, frames_dir: Path, export_request) -> None:
            frames_dir.mkdir(parents=True, exist_ok=True)
            background_alpha = 0 if bool(export_request.alpha) else 255
            for frame_index in range(export_request.frames):
                image = Image.new("RGBA", (export_request.width, export_request.height), (0, 0, 0, background_alpha))
                draw = ImageDraw.Draw(image, "RGBA")
                drift = int(round(frame_index * max(export_request.width // max(export_request.frames, 1), 1)))
                draw.ellipse(
                    (
                        int(export_request.width * 0.52),
                        int(export_request.height * 0.18),
                        int(export_request.width * 0.84),
                        int(export_request.height * 0.78),
                    ),
                    fill=(214, 214, 214, 228),
                )
                draw.ellipse(
                    (
                        max(0, int(export_request.width * 0.18) - drift),
                        int(export_request.height * 0.40),
                        max(1, int(export_request.width * 0.48) - drift),
                        int(export_request.height * 0.68),
                    ),
                    fill=(92, 92, 92, 188),
                )
                image.save(frames_dir / f"frame_{frame_index:05d}.png")

        return export

    def _fake_primary_encode(self):
        def encode(_frames_dir: Path, _fps: int, output_path: Path, *, alpha: bool = False) -> None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text("video", encoding="utf-8")

        return encode

    def _fake_master_encode(self):
        def encode(_frames_dir: Path, _fps: int, output_path: Path) -> None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text("master", encoding="utf-8")

        return encode

    def test_init_project_bundle_auto_approves_alpha_mask(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_image = self._write_isolated_source_image(root)
            args = self._init_args(root, source_image)

            project = init_project_bundle(args)
            loaded = load_project(Path(args.project))
            mask_paths = project_mask_paths(Path(args.project), loaded["active_source_id"])

            self.assertEqual(project["project_id"], "adhoc_hero_subject_test")
            self.assertEqual(loaded["scene"]["seed"], 4242)
            self.assertEqual(loaded["mask"]["status"], MASK_STATUS_APPROVED)
            self.assertEqual(loaded["mask"]["source"], "alpha")
            self.assertEqual(len(loaded["source_candidates"]), 1)
            self.assertEqual(loaded["active_source_id"], "source_01")
            self.assertEqual(loaded["source_candidates"][0]["origin"], "init")
            self.assertTrue(Path(loaded["source_candidates"][0]["path"]).exists())
            self.assertTrue(mask_paths.proposal.exists())
            self.assertTrue(mask_paths.approved.exists())
            self.assertTrue(project_mask_paths(Path(args.project)).approved.exists())
            self.assertTrue(loaded["subject_analysis"]["alpha_present"])
            self.assertIsNotNone(loaded["subject_analysis"]["subject_bounds"])
            self.assertTrue((loaded["subject_analysis"]["coverage_ratio"] or 0.0) > 0.0)

    def test_init_project_bundle_creates_review_required_mask_for_scenic_image(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_image = self._write_scenic_source_image(root)
            args = self._init_args(root, source_image)

            with mock.patch("workbench_tool.generate_auto_proposal_mask", return_value=(self._proposal_mask((960, 540)), "vision_saliency")):
                project = init_project_bundle(args)

            loaded = load_project(Path(args.project))
            mask_paths = project_mask_paths(Path(args.project), loaded["active_source_id"])
            self.assertEqual(project["mask"]["status"], MASK_STATUS_REVIEW_REQUIRED)
            self.assertEqual(project["mask"]["source"], "auto_model")
            self.assertEqual(project["mask"]["proposal_engine"], "vision_saliency")
            self.assertTrue(mask_paths.proposal.exists())
            self.assertTrue(mask_paths.approved.exists())
            self.assertIsNone(loaded["subject_analysis"]["subject_bounds"])
            self.assertIsNone(loaded["subject_analysis"]["coverage_ratio"])

    def test_init_project_bundle_allows_model_only_projects(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            args = self._init_args(root, None, behavior="A spacecraft model erupts into monochrome particles.")

            project = init_project_bundle(args)
            loaded = load_project(Path(args.project))

            self.assertEqual(project["workflow_mode"], "model_only")
            self.assertEqual(loaded["workflow_mode"], "model_only")
            self.assertEqual(loaded["active_source_id"], "")
            self.assertEqual(loaded["source_candidates"], [])
            self.assertEqual(loaded["scene"]["volume_backend"], VOLUME_BACKEND_MODEL_SOURCE)
            self.assertEqual(loaded["model_source"]["status"], "idle")
            self.assertEqual(loaded["mask"]["status"], "not_applicable")
            self.assertEqual(loaded["approval"]["status"], "draft")

    def test_init_project_bundle_preloads_builtin_challenger_model_for_shuttle_objective(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            args = self._init_args(root, None, behavior="The Challenger space shuttle dissolves into monochrome particles.")
            args.episode_id = "challenger"
            args.motion_item_id = "challenger_space_shuttle"

            project = init_project_bundle(args)
            loaded = load_project(Path(args.project))

            self.assertEqual(project["workflow_mode"], "model_only")
            self.assertEqual(loaded["scene"]["volume_backend"], VOLUME_BACKEND_MODEL_SOURCE)
            self.assertEqual(loaded["model_source"]["status"], MODEL_SOURCE_STATUS_SELECTED)
            self.assertEqual(loaded["model_source"]["provider"], "builtin_curated")
            self.assertEqual(loaded["model_source"]["remote_id"], "challenger_shuttle_stack")
            self.assertEqual(loaded["model_source"]["title"], "Challenger Shuttle Stack")
            self.assertTrue(Path(loaded["model_source"]["raw_asset_path"]).exists())
            self.assertTrue(Path(loaded["model_source"]["point_cache_path"]).exists())
            self.assertEqual(loaded["approval"]["status"], "draft")

    def test_load_project_recovers_default_draft_harness_to_builtin_challenger_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            args = self._init_args(root, None, behavior="The Challenger space shuttle dissolves into monochrome particles.")
            args.episode_id = "challenger"
            args.motion_item_id = "challenger_space_shuttle"
            init_project_bundle(args)
            project_path = Path(args.project)

            raw_project = json.loads(project_path.read_text(encoding="utf-8"))
            raw_project["scene"]["preset_family"] = "collision"
            raw_project["scene"]["breakup"]["amount"] = 0.02
            raw_project["scene"]["breakup"]["retain"] = 1.0
            raw_project["model_source"]["provider"] = "poly_pizza"
            raw_project["model_source"]["remote_id"] = "VSxUAFhzbA"
            raw_project["model_source"]["title"] = "Spaceship"
            project_path.write_text(json.dumps(raw_project, indent=2) + "\n", encoding="utf-8")

            with mock.patch.object(workbench_tool_module, "VISIBLE_DRIFT_DEFAULT_HARNESS_PROJECT_PATH", project_path):
                recovered = load_project(project_path)

            self.assertEqual(recovered["model_source"]["provider"], "builtin_curated")
            self.assertEqual(recovered["model_source"]["remote_id"], "challenger_shuttle_stack")
            self.assertAlmostEqual(recovered["scene"]["breakup"]["amount"], PRESET_DEFAULTS["collision"]["breakup"]["amount"], places=3)
            self.assertLess(recovered["scene"]["breakup"]["retain"], 1.0)

    def test_upload_project_model_source_supports_model_only_projects(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_model = self._write_cube_obj(root)
            args = self._init_args(root, None, behavior="A shuttle model dissolves into monochrome particles.")
            init_project_bundle(args)

            updated = upload_project_model_source(Path(args.project), self._model_upload_payload(raw_model, label="Orbiter Mesh"))

            self.assertEqual(updated["scene"]["volume_backend"], VOLUME_BACKEND_MODEL_SOURCE)
            self.assertEqual(updated["model_source"]["status"], MODEL_SOURCE_STATUS_SELECTED)
            self.assertEqual(updated["model_source"]["provider"], "local_upload")
            self.assertEqual(updated["model_source"]["title"], "Orbiter Mesh")
            self.assertTrue(Path(updated["model_source"]["point_cache_path"]).exists())
            self.assertEqual(updated["approval"]["status"], "draft")

    def test_load_project_does_not_auto_reset_approved_model_only_project(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_model = self._write_cube_obj(root)
            args = self._init_args(root, None, behavior="A shuttle model dissolves into monochrome particles.")
            init_project_bundle(args)
            project_path = Path(args.project)
            upload_project_model_source(project_path, self._model_upload_payload(raw_model, label="Shuttle Mesh"))
            approve_project_look(project_path)

            raw_project = json.loads(project_path.read_text(encoding="utf-8"))
            raw_project["scene"]["breakup"]["amount"] = 0.02
            raw_project["scene"]["breakup"]["retain"] = 1.0
            raw_project["model_source"]["provider"] = "local_upload"
            project_path.write_text(json.dumps(raw_project, indent=2) + "\n", encoding="utf-8")

            loaded = load_project(project_path)

            self.assertEqual(loaded["approval"]["status"], "approved")
            self.assertEqual(loaded["scene"]["breakup"]["amount"], 0.02)
            self.assertEqual(loaded["scene"]["breakup"]["retain"], 1.0)
            self.assertEqual(loaded["model_source"]["provider"], "local_upload")

    def test_load_project_recovers_suppressed_nondefault_model_only_project_without_replacing_model(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_model = self._write_cube_obj(root)
            args = self._init_args(root, None, behavior="A shuttle model dissolves into monochrome particles.")
            init_project_bundle(args)
            project_path = Path(args.project)
            upload_project_model_source(project_path, self._model_upload_payload(raw_model, label="Shuttle Mesh"))

            raw_project = json.loads(project_path.read_text(encoding="utf-8"))
            raw_project["scene"]["preset_family"] = "memory"
            raw_project["scene"]["breakup"]["amount"] = 0.01
            raw_project["scene"]["breakup"]["retain"] = 1.0
            raw_project["scene"]["surface"]["density"] = 2.8
            project_path.write_text(json.dumps(raw_project, indent=2) + "\n", encoding="utf-8")

            loaded = load_project(project_path)

            self.assertEqual(loaded["model_source"]["provider"], "local_upload")
            self.assertAlmostEqual(loaded["scene"]["breakup"]["amount"], PRESET_DEFAULTS["memory"]["breakup"]["amount"], places=3)
            self.assertAlmostEqual(loaded["scene"]["surface"]["density"], PRESET_DEFAULTS["memory"]["surface"]["density"], places=3)

    def test_add_source_candidate_uploads_project_local_candidate_and_selects_it(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            init_source = self._write_isolated_source_image(root)
            candidate_source = self._write_scenic_source_image(root)
            args = self._init_args(root, init_source)
            init_project_bundle(args)
            project_path = Path(args.project)

            with mock.patch("workbench_tool.generate_auto_proposal_mask", return_value=(self._proposal_mask((960, 540)), "vision_saliency")):
                updated = add_source_candidate(project_path, self._upload_payload(candidate_source, label="Launch Candidate"))

            self.assertEqual(updated["active_source_id"], "source_02")
            self.assertEqual(len(updated["source_candidates"]), 2)
            active_candidate = next(candidate for candidate in updated["source_candidates"] if candidate["id"] == "source_02")
            self.assertEqual(active_candidate["origin"], "upload")
            self.assertEqual(active_candidate["label"], "Launch Candidate")
            self.assertTrue(Path(active_candidate["path"]).exists())
            self.assertTrue(str(Path(active_candidate["path"])).startswith(str(project_path.parent / "sources")))
            self.assertEqual(active_candidate["mask"]["status"], MASK_STATUS_REVIEW_REQUIRED)
            self.assertTrue(project_mask_paths(project_path, "source_02").proposal.exists())

    def test_select_source_candidate_resets_scene_for_selected_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            init_source = self._write_isolated_source_image(root)
            candidate_source = self._write_scenic_source_image(root)
            args = self._init_args(root, init_source)
            init_project_bundle(args)
            project_path = Path(args.project)

            with mock.patch("workbench_tool.generate_auto_proposal_mask", return_value=(self._proposal_mask((960, 540)), "vision_saliency")):
                add_source_candidate(project_path, self._upload_payload(candidate_source))
            apply_project_patch(
                project_path,
                {
                    "scene": {
                        "camera": {"yaw": 1.1, "pitch": 0.44, "distance": 1.65},
                        "surface": {"density": 1.31},
                    }
                },
            )

            selected = select_source_candidate(project_path, "source_01")

            self.assertEqual(selected["active_source_id"], "source_01")
            self.assertNotAlmostEqual(selected["scene"]["camera"]["yaw"], 1.1, places=2)
            self.assertNotAlmostEqual(selected["scene"]["surface"]["density"], 1.31, places=2)
            self.assertEqual(selected["active_snapshot_id"], "snapshot_initial")
            self.assertEqual(len(selected["snapshots"]), 1)

    def test_remove_source_candidate_updates_candidate_list(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            init_source = self._write_isolated_source_image(root)
            candidate_source = self._write_scenic_source_image(root)
            args = self._init_args(root, init_source)
            init_project_bundle(args)
            project_path = Path(args.project)

            with mock.patch("workbench_tool.generate_auto_proposal_mask", return_value=(self._proposal_mask((960, 540)), "vision_saliency")):
                add_source_candidate(project_path, self._upload_payload(candidate_source))
            select_source_candidate(project_path, "source_01")
            candidate_path = Path(load_project(project_path)["source_candidates"][1]["path"])
            candidate_mask_root = project_mask_paths(project_path, "source_02").root

            updated = remove_source_candidate(project_path, "source_02")

            self.assertEqual(updated["active_source_id"], "source_01")
            self.assertEqual([candidate["id"] for candidate in updated["source_candidates"]], ["source_01"])
            self.assertFalse(candidate_path.exists())
            self.assertFalse(candidate_mask_root.exists())

    def test_mask_brush_and_approve_update_subject_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_image = self._write_scenic_source_image(root)
            args = self._init_args(root, source_image)

            with mock.patch("workbench_tool.generate_auto_proposal_mask", return_value=(self._proposal_mask((960, 540)), "vision_saliency")):
                init_project_bundle(args)

            project_path = Path(args.project)
            apply_mask_brush(
                project_path,
                {
                    "mode": "add",
                    "radius": 0.03,
                    "points": [{"x": 0.70, "y": 0.78}, {"x": 0.72, "y": 0.82}],
                },
            )
            brushed = load_project(project_path)
            self.assertEqual(brushed["mask"]["status"], MASK_STATUS_REVIEW_REQUIRED)
            self.assertEqual(brushed["mask"]["source"], "manual_refine")

            approve_mask(project_path)
            approved = load_project(project_path)
            self.assertEqual(approved["mask"]["status"], MASK_STATUS_APPROVED)
            self.assertIsNotNone(approved["subject_analysis"]["subject_bounds"])
            self.assertTrue((approved["subject_analysis"]["coverage_ratio"] or 0.0) > 0.0)

            with Image.open(project_mask_paths(project_path, approved["active_source_id"]).approved) as mask:
                self.assertIsNotNone(mask.getbbox())

    def test_effect_scene_payload_is_deterministic_for_fixed_project(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_image = self._write_isolated_source_image(root)
            args = self._init_args(root, source_image)
            init_project_bundle(args)
            project_path = Path(args.project)

            first = build_effect_scene_payload(project_path, load_project(project_path))
            second = build_effect_scene_payload(project_path, load_project(project_path))

            self.assertEqual(first, second)
            self.assertEqual(first["source_id"], "source_01")
            self.assertEqual(first["scene"]["effect_model"], DEFAULT_EFFECT_MODEL)
            self.assertIn("brightness", first["point_schema"])
            self.assertIn("alpha_base", first["point_schema"])
            self.assertIn("alpha_decay", first["point_schema"])
            self.assertIn("motion_mode", first["point_schema"])
            self.assertEqual(first["raw_model_mesh"]["format"], "mesh_v1")
            self.assertEqual(first["raw_model_mesh"]["meshes"], [])
            self.assertEqual(first["raw_model_mesh"]["visibility_points"], [])
            self.assertEqual(first["raw_model_schema"], ["x", "y", "z", "radius", "brightness", "alpha"])
            self.assertEqual(first["raw_model_points"], [])
            self.assertEqual(first["raw_model_fit_camera"], load_project(project_path)["scene"]["camera"])
            self.assertTrue(len(first["points"]) > 0)

    def test_shuttle_prior_assist_activates_for_matching_shuttle_subject(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_image = self._write_shuttle_stack_source_image(root)
            args = self._init_args(
                root,
                source_image,
                behavior="The space shuttle orbiter dissolves into monochrome particles.",
            )

            init_project_bundle(args)
            loaded = load_project(Path(args.project))
            prior_assist = loaded["prior_assist"]

            self.assertEqual(prior_assist["status"], PRIOR_ASSIST_STATUS_ACTIVE)
            self.assertEqual(prior_assist["subject_class"], "space_shuttle")
            self.assertEqual(prior_assist["source"], "curated_local_prior")
            self.assertTrue(prior_assist["prior_id"].startswith("space_shuttle_"))
            self.assertGreaterEqual(prior_assist["fit_score"], 0.70)

            effect_scene = build_effect_scene_payload(Path(args.project), loaded)
            self.assertEqual(effect_scene["prior_assist"]["status"], PRIOR_ASSIST_STATUS_ACTIVE)

    def test_non_shuttle_subject_keeps_prior_assist_inactive(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_image = self._write_isolated_source_image(root)
            args = self._init_args(root, source_image)

            init_project_bundle(args)
            loaded = load_project(Path(args.project))

            self.assertEqual(loaded["prior_assist"]["status"], PRIOR_ASSIST_STATUS_INACTIVE)
            self.assertEqual(loaded["prior_assist"]["reason"], PRIOR_ASSIST_REASON_NOT_ELIGIBLE)

    def test_shuttle_eligible_but_low_fit_subject_rejects_prior_assist(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_image = self._write_isolated_source_image(root)
            args = self._init_args(
                root,
                source_image,
                behavior="The shuttle orbiter dissolves into monochrome particles.",
            )

            init_project_bundle(args)
            loaded = load_project(Path(args.project))

            self.assertEqual(loaded["prior_assist"]["status"], PRIOR_ASSIST_STATUS_REJECTED)
            self.assertEqual(loaded["prior_assist"]["reason"], PRIOR_ASSIST_REASON_LOW_FIT)

    def test_shuttle_prior_assist_preserves_source_xy_and_expands_depth_spread(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_image = self._write_shuttle_stack_source_image(root)
            args = self._init_args(
                root,
                source_image,
                behavior="The space shuttle orbiter dissolves into monochrome particles.",
            )

            init_project_bundle(args)
            project_path = Path(args.project)
            project, plain_particles = self._particles_for_project(project_path)
            _loaded, active_particles = self._active_particles_for_project(project_path)

            self.assertEqual(len(active_particles), len(plain_particles))
            self.assertEqual(
                [(round(p["source_x"], 4), round(p["source_y"], 4)) for p in plain_particles],
                [(round(p["source_x"], 4), round(p["source_y"], 4)) for p in active_particles],
            )

            plain_z_span = max(p["world_z"] for p in plain_particles) - min(p["world_z"] for p in plain_particles)
            active_z_span = max(p["world_z"] for p in active_particles) - min(p["world_z"] for p in active_particles)
            self.assertGreater(active_z_span, plain_z_span * 1.12)

            width = int(project["motion_contract"]["width"])
            height = int(project["motion_contract"]["height"])
            camera_a = camera_vectors(project["scene"]["camera"])
            shifted_camera = dict(project["scene"]["camera"])
            shifted_camera["yaw"] = float(shifted_camera["yaw"]) + 0.34
            camera_b = camera_vectors(shifted_camera)

            def average_parallax(particles: list[dict[str, float]]) -> float:
                deltas = []
                for particle in particles:
                    if particle["layer"] != "shell":
                        continue
                    projected_a = project_point((particle["world_x"], particle["world_y"], particle["world_z"]), camera_a, width, height)
                    projected_b = project_point((particle["world_x"], particle["world_y"], particle["world_z"]), camera_b, width, height)
                    if projected_a is None or projected_b is None:
                        continue
                    deltas.append(((projected_b[0] - projected_a[0]) ** 2 + (projected_b[1] - projected_a[1]) ** 2) ** 0.5)
                return sum(deltas) / max(len(deltas), 1)

            self.assertGreater(average_parallax(active_particles), average_parallax(plain_particles) * 1.05)

    def test_search_project_model_sources_returns_provider_results(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_image = self._write_isolated_source_image(root)
            args = self._init_args(root, source_image)
            init_project_bundle(args)

            with mock.patch(
                "workbench_tool.search_model_candidates",
                return_value=[
                    {
                        "provider": "nasa_3d",
                        "provider_label": "NASA 3D",
                        "remote_id": "crawler",
                        "remote_url": "https://science.nasa.gov/3d-resources/crawler/",
                        "title": "Crawler",
                        "preview_url": "https://science.nasa.gov/crawler-thumb.jpg",
                        "license_class": "nasa_media_guidelines",
                        "status": "search_result",
                    }
                ],
            ):
                results = search_project_model_sources(Path(args.project), {"query": "crawler"})

            self.assertEqual(results["query"], "crawler")
            self.assertEqual(len(results["results"]), 1)
            self.assertEqual(results["results"][0]["provider"], "nasa_3d")
            self.assertEqual(results["results"][0]["preview_url"], "https://science.nasa.gov/crawler-thumb.jpg")
            self.assertEqual(len(results["resources"]), 4)
            self.assertEqual(results["resources"][0]["label"], "CGTrader")
            self.assertIn("crawler", results["resources"][0]["search_url"])

    def test_select_model_source_switches_backend_and_writes_project_local_assets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_image = self._write_isolated_source_image(root)
            raw_model = self._write_cube_obj(root)
            args = self._init_args(root, source_image)
            init_project_bundle(args)
            project_path = Path(args.project)

            response = select_project_model_source(
                project_path,
                {
                    "candidate": {
                        "query": "crawler",
                        "provider": "nasa_3d",
                        "provider_label": "NASA 3D",
                        "remote_id": "crawler",
                        "remote_url": "https://science.nasa.gov/3d-resources/crawler/",
                        "title": "Crawler",
                        "license_class": "nasa_media_guidelines",
                        "status": "fetched",
                        "raw_asset_path": str(raw_model),
                        "source_format": "obj",
                    }
                },
            )
            selected = response["project"]

            self.assertEqual(selected["scene"]["volume_backend"], VOLUME_BACKEND_MODEL_SOURCE)
            self.assertEqual(selected["scene"]["emitter"]["direction_space"], "subject")
            self.assertEqual(selected["model_source"]["status"], MODEL_SOURCE_STATUS_SELECTED)
            self.assertEqual(selected["model_source"]["provider_kind"], "open_access")
            self.assertEqual(selected["model_source"]["provider_capability"], "enabled")
            self.assertEqual(selected["model_source"]["subject_fit"], "real_world")
            self.assertTrue(Path(selected["model_source"]["raw_asset_path"]).exists())
            self.assertTrue(Path(selected["model_source"]["normalized_asset_path"]).exists())
            self.assertTrue(Path(selected["model_source"]["point_cache_path"]).exists())

    def test_select_sketchfab_model_source_persists_attribution_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_image = self._write_isolated_source_image(root)
            raw_model = self._write_cube_obj(root)
            args = self._init_args(root, source_image)
            init_project_bundle(args)
            project_path = Path(args.project)

            response = select_project_model_source(
                project_path,
                {
                    "candidate": {
                        "query": "face",
                        "provider": "sketchfab",
                        "provider_label": "Sketchfab",
                        "remote_id": "face-cc0",
                        "remote_url": "https://sketchfab.com/3d-models/face-cc0",
                        "title": "Face Scan",
                        "license_class": "cc0",
                        "license_summary": "CC0",
                        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
                        "author_name": "Artist One",
                        "author_url": "https://sketchfab.com/artist-one",
                        "attribution_text": "Face Scan by Artist One via Sketchfab (CC0)",
                        "status": "fetched",
                        "raw_asset_path": str(raw_model),
                        "source_format": "obj",
                        "requires_auth": True,
                    }
                },
            )
            selected = response["project"]["model_source"]

            self.assertEqual(selected["provider"], "sketchfab")
            self.assertEqual(selected["author_name"], "Artist One")
            self.assertEqual(selected["license_url"], "https://creativecommons.org/publicdomain/zero/1.0/")
            self.assertIn("Sketchfab", selected["attribution_text"])

    def test_model_source_effect_scene_payload_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_image = self._write_isolated_source_image(root)
            raw_model = self._write_cube_obj(root)
            args = self._init_args(root, source_image)
            init_project_bundle(args)
            project_path = Path(args.project)
            select_project_model_source(
                project_path,
                {
                    "candidate": {
                        "query": "face",
                        "provider": "sketchfab",
                        "provider_label": "Sketchfab",
                        "remote_id": "face-cc0",
                        "remote_url": "https://sketchfab.com/3d-models/face-cc0",
                        "title": "Face Scan",
                        "license_class": "cc0",
                        "license_summary": "CC0",
                        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
                        "author_name": "Artist One",
                        "author_url": "https://sketchfab.com/artist-one",
                        "attribution_text": "Face Scan by Artist One via Sketchfab (CC0)",
                        "status": "fetched",
                        "raw_asset_path": str(raw_model),
                        "source_format": "obj",
                        "requires_auth": True,
                    }
                },
            )

            first = build_effect_scene_payload(project_path, load_project(project_path))
            second = build_effect_scene_payload(project_path, load_project(project_path))

            self.assertEqual(first, second)
            self.assertEqual(first["scene"]["volume_backend"], VOLUME_BACKEND_MODEL_SOURCE)
            self.assertEqual(first["model_source"]["provider"], "sketchfab")
            self.assertIn("motion_mode", first["point_schema"])
            motion_mode_index = first["point_schema"].index("motion_mode")
            motion_modes = {int(point[motion_mode_index]) for point in first["points"]}
            self.assertEqual(
                motion_modes,
                {
                    PARTICLE_MOTION_ANCHOR_SHELL,
                    PARTICLE_MOTION_ANCHOR_ATTACHMENT,
                    PARTICLE_MOTION_EMISSION_PLUME,
                },
            )
            self.assertTrue(len(first["points"]) > 0)
            self.assertEqual(first["raw_model_mesh"]["format"], "mesh_v1")
            self.assertTrue(len(first["raw_model_mesh"]["meshes"]) > 0)
            self.assertTrue(len(first["raw_model_mesh"]["visibility_points"]) > 0)
            self.assertIn("positions", first["raw_model_mesh"]["meshes"][0])
            self.assertIn("material", first["raw_model_mesh"]["meshes"][0])
            self.assertEqual(first["raw_model_schema"], ["x", "y", "z", "radius", "brightness", "alpha"])
            self.assertTrue(len(first["raw_model_points"]) > 0)
            self.assertNotEqual(first["raw_model_fit_camera"], {})
            self.assertIn("distance", first["raw_model_fit_camera"])
            self.assertEqual(first["scene"]["emitter"]["direction_space"], "subject")
            self.assertEqual(first["model_source"]["subject_frame"]["space"], "model")

    def test_model_source_rotation_patch_rotates_subject_frame_and_emitter_axis(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_image = self._write_isolated_source_image(root)
            raw_model = self._write_wedge_obj(root)
            args = self._init_args(root, source_image)
            init_project_bundle(args)
            project_path = Path(args.project)
            upload_project_model_source(project_path, self._model_upload_payload(raw_model, label="Wedge Mesh"))

            baseline = build_effect_scene_payload(project_path, load_project(project_path))
            self.assertEqual(baseline["model_source"]["subject_frame"]["longitudinal_axis"], "x")
            self.assertGreater(abs(float(baseline["scene"]["emitter"]["direction_x"])), 0.9)
            self.assertLess(abs(float(baseline["scene"]["emitter"]["direction_z"])), 0.1)

            updated = apply_project_patch(
                project_path,
                {
                    "model_source": {
                        "transform": {
                            "rotate_y_deg": 450.0,
                        }
                    }
                },
            )

            self.assertAlmostEqual(updated["model_source"]["transform"]["rotate_y_deg"], 450.0, places=3)
            rotated = build_effect_scene_payload(project_path, load_project(project_path))
            self.assertAlmostEqual(rotated["model_source"]["transform"]["rotate_y_deg"], 450.0, places=3)
            self.assertEqual(rotated["model_source"]["subject_frame"]["longitudinal_axis"], "z")
            self.assertGreater(abs(float(rotated["scene"]["emitter"]["direction_z"])), 0.9)
            self.assertLess(abs(float(rotated["scene"]["emitter"]["direction_x"])), 0.1)
            self.assertNotEqual(
                baseline["raw_model_mesh"]["visibility_points"][:12],
                rotated["raw_model_mesh"]["visibility_points"][:12],
            )
            self.assertNotEqual(
                baseline["raw_model_points"][:12],
                rotated["raw_model_points"][:12],
            )

    def test_upload_model_source_initializes_scene_camera_from_canonical_reset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_model = self._write_wedge_obj(root)
            args = self._init_args(root, None, behavior="A shuttle model dissolves into monochrome particles.")
            init_project_bundle(args)
            project_path = Path(args.project)

            updated = upload_project_model_source(project_path, self._model_upload_payload(raw_model, label="Wedge Mesh"))
            payload = build_effect_scene_payload(project_path, load_project(project_path))

            self.assertEqual(updated["scene"]["camera"], payload["reset_camera"])
            self.assertIn("roll", payload["reset_camera"])
            self.assertIn("roll", payload["raw_model_reset_camera"])
            self.assertEqual(payload["camera"], payload["reset_camera"])

    def test_model_source_reset_cameras_follow_transformed_subject_orientation(self) -> None:
        def dot(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
            return float(a[0] * b[0]) + float(a[1] * b[1]) + float(a[2] * b[2])

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_model = self._write_wedge_obj(root)
            args = self._init_args(root, None, behavior="A shuttle model dissolves into monochrome particles.")
            init_project_bundle(args)
            project_path = Path(args.project)
            upload_project_model_source(project_path, self._model_upload_payload(raw_model, label="Wedge Mesh"))

            baseline = build_effect_scene_payload(project_path, load_project(project_path))
            baseline_reset_basis = camera_vectors(baseline["reset_camera"])

            apply_project_patch(
                project_path,
                {
                    "model_source": {
                        "transform": {
                            "rotate_x_deg": 90.0,
                        }
                    }
                },
            )
            rotated = build_effect_scene_payload(project_path, load_project(project_path))
            rotated_reset_basis = camera_vectors(rotated["reset_camera"])

            expected_forward = rotate_model_source_vector(
                baseline_reset_basis["forward"],
                {"rotate_x_deg": 90.0},
            )
            expected_up = rotate_model_source_vector(
                baseline_reset_basis["up"],
                {"rotate_x_deg": 90.0},
            )

            self.assertIn("reset_camera", rotated)
            self.assertIn("raw_model_reset_camera", rotated)
            self.assertGreater(abs(float(rotated["reset_camera"]["roll"])), 1.4)
            self.assertGreater(abs(float(rotated["raw_model_reset_camera"]["roll"])), 1.4)
            self.assertGreater(dot(rotated_reset_basis["forward"], expected_forward), 0.97)
            self.assertGreater(dot(rotated_reset_basis["up"], expected_up), 0.97)

    def test_subject_frame_heuristic_detects_builtin_shuttle_aft_axis(self) -> None:
        stack_payload = json.loads((ROOT / "config" / "workbench_priors" / "space_shuttle_stack_v1.points.json").read_text(encoding="utf-8"))
        orbiter_payload = json.loads((ROOT / "config" / "workbench_priors" / "space_shuttle_orbiter_side_v1.points.json").read_text(encoding="utf-8"))

        stack_frame = infer_subject_frame_from_points(stack_payload["points"])
        orbiter_frame = infer_subject_frame_from_points(orbiter_payload["points"])

        self.assertEqual(stack_frame["longitudinal_axis"], "y")
        self.assertEqual(stack_frame["aft_sign"], 1)
        self.assertEqual(stack_frame["default_emitter_direction"]["y"], 1.0)
        self.assertEqual(orbiter_frame["longitudinal_axis"], "x")
        self.assertEqual(orbiter_frame["aft_sign"], -1)
        self.assertEqual(orbiter_frame["default_emitter_direction"]["x"], -1.0)

    def test_model_only_init_assigns_subject_relative_emitter_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            args = self._init_args(root, None, behavior="A shuttle orbiter dissolves into monochrome particles.")

            init_project_bundle(args)
            project = load_project(Path(args.project))

            self.assertEqual(project["scene"]["volume_backend"], VOLUME_BACKEND_MODEL_SOURCE)
            self.assertEqual(project["scene"]["emitter"]["direction_space"], "subject")
            self.assertEqual(project["model_source"]["status"], MODEL_SOURCE_STATUS_SELECTED)
            self.assertTrue(Path(project["model_source"]["point_cache_path"]).exists())

    def test_model_density_above_one_spawns_supplemental_particles(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_model = self._write_cube_obj(root)
            args = self._init_args(root, None, behavior="A shuttle model dissolves into monochrome particles.")
            init_project_bundle(args)
            project_path = Path(args.project)
            upload_project_model_source(project_path, self._model_upload_payload(raw_model, label="Shuttle Mesh"))

            apply_project_patch(project_path, {"scene": {"surface": {"density": 1.0}}})
            density_one = generate_active_particle_specs(project_path, load_project(project_path))

            apply_project_patch(project_path, {"scene": {"surface": {"density": 3.0}}})
            density_three = generate_active_particle_specs(project_path, load_project(project_path))

            def count_by_motion_mode(particles: list[dict[str, float]]) -> dict[int, int]:
                counts = {
                    PARTICLE_MOTION_ANCHOR_SHELL: 0,
                    PARTICLE_MOTION_ANCHOR_ATTACHMENT: 0,
                    PARTICLE_MOTION_EMISSION_PLUME: 0,
                }
                for particle in particles:
                    counts[int(particle["motion_mode"])] = counts.get(int(particle["motion_mode"]), 0) + 1
                return counts

            counts_one = count_by_motion_mode(density_one)
            counts_three = count_by_motion_mode(density_three)

            self.assertEqual(counts_three[PARTICLE_MOTION_ANCHOR_SHELL], counts_one[PARTICLE_MOTION_ANCHOR_SHELL])
            self.assertEqual(counts_three[PARTICLE_MOTION_ANCHOR_ATTACHMENT], counts_one[PARTICLE_MOTION_ANCHOR_ATTACHMENT])
            self.assertGreater(counts_three[PARTICLE_MOTION_EMISSION_PLUME], counts_one[PARTICLE_MOTION_EMISSION_PLUME] * 2.5)
            self.assertLess(counts_three[PARTICLE_MOTION_EMISSION_PLUME], counts_one[PARTICLE_MOTION_EMISSION_PLUME] * 5.0)

    def test_reset_to_preset_baseline_replaces_stale_effect_values_but_keeps_camera(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_model = self._write_cube_obj(root)
            args = self._init_args(root, None, behavior="A shuttle model dissolves into monochrome particles.")
            init_project_bundle(args)
            project_path = Path(args.project)
            upload_project_model_source(project_path, self._model_upload_payload(raw_model, label="Shuttle Mesh"))

            apply_project_patch(
                project_path,
                {
                    "scene": {
                        "camera": {"yaw": 1.14, "pitch": 0.34, "distance": 2.45},
                        "breakup": {"amount": 0.18, "retain": 0.88},
                        "surface": {"density": 2.9},
                    }
                },
            )

            updated = apply_project_patch(
                project_path,
                {
                    "scene": {"preset_family": "vigil"},
                    "reset_to_preset": True,
                },
            )

            self.assertAlmostEqual(updated["scene"]["camera"]["yaw"], 1.14, places=2)
            self.assertAlmostEqual(updated["scene"]["camera"]["pitch"], 0.34, places=2)
            self.assertAlmostEqual(updated["scene"]["breakup"]["amount"], PRESET_DEFAULTS["vigil"]["breakup"]["amount"], places=3)
            self.assertAlmostEqual(updated["scene"]["surface"]["density"], PRESET_DEFAULTS["vigil"]["surface"]["density"], places=3)
            self.assertEqual(updated["scene"]["emitter"]["direction_space"], "subject")

    def test_save_project_preset_overwrites_case_insensitively_and_apply_preserves_camera_and_shot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_model = self._write_cube_obj(root)
            args = self._init_args(root, None, behavior="A shuttle model dissolves into monochrome particles.")
            init_project_bundle(args)
            project_path = Path(args.project)
            upload_project_model_source(project_path, self._model_upload_payload(raw_model, label="Shuttle Mesh"))

            apply_project_patch(
                project_path,
                {
                    "scene": {
                        "surface": {"density": 1.36},
                        "breakup": {"amount": 0.41},
                        "render": {"contrast": 1.31},
                    }
                },
            )
            first_saved = save_project_preset(project_path, "Signature")
            preset_id = first_saved["active_preset_id"]

            apply_project_patch(
                project_path,
                {
                    "scene": {
                        "surface": {"density": 0.84},
                        "breakup": {"amount": 0.52},
                        "render": {"contrast": 0.94},
                    }
                },
            )
            overwritten = save_project_preset(project_path, "signature")

            self.assertEqual(len(overwritten["saved_presets"]), 1)
            self.assertEqual(overwritten["saved_presets"][0]["id"], preset_id)
            self.assertAlmostEqual(overwritten["saved_presets"][0]["effect"]["surface"]["density"], 0.84, places=3)
            self.assertAlmostEqual(overwritten["saved_presets"][0]["effect"]["render"]["contrast"], 0.94, places=3)

            apply_project_patch(
                project_path,
                {
                    "scene": {
                        "camera": {"yaw": 0.91, "pitch": 0.27, "distance": 2.18},
                        "shot": {"frames": 120, "fps": 30, "duration_seconds": 4.0},
                        "surface": {"density": 0.52},
                    }
                },
            )
            applied = apply_project_preset(project_path, preset_id)

            self.assertEqual(applied["active_preset_id"], preset_id)
            self.assertEqual(applied["approval"]["status"], "draft")
            self.assertAlmostEqual(applied["scene"]["surface"]["density"], 0.84, places=3)
            self.assertAlmostEqual(applied["scene"]["breakup"]["amount"], 0.52, places=3)
            self.assertAlmostEqual(applied["scene"]["render"]["contrast"], 0.94, places=3)
            self.assertAlmostEqual(applied["scene"]["camera"]["yaw"], 0.91, places=2)
            self.assertAlmostEqual(applied["scene"]["camera"]["pitch"], 0.27, places=2)
            self.assertEqual(applied["scene"]["shot"]["frames"], 120)
            self.assertEqual(applied["scene"]["shot"]["fps"], 30)
            self.assertEqual(applied["scene"]["shot"]["duration_seconds"], 4.0)

    def test_model_directional_drift_bias_releases_downwind_side_earlier(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_model = self._write_cube_obj(root)
            args = self._init_args(root, None, behavior="A shuttle model dissolves into monochrome particles.")
            init_project_bundle(args)
            project_path = Path(args.project)
            upload_project_model_source(project_path, self._model_upload_payload(raw_model, label="Shuttle Mesh"))
            apply_project_patch(
                project_path,
                {
                    "scene": {
                        "breakup": {
                            "amount": 0.44,
                            "tail": 0.62,
                            "drift_x": 0.92,
                            "drift_y": 0.0,
                        },
                        "emitter": {
                            "direction_x": 1.0,
                            "direction_y": 0.0,
                            "direction_z": 0.0,
                        },
                    }
                },
            )

            project = load_project(project_path)
            particles = generate_active_particle_specs(project_path, project)
            shell_particles = [particle for particle in particles if particle["layer"] == "shell"]
            emission_particles = [particle for particle in particles if particle["layer"] == "emission"]
            downwind = max(shell_particles, key=lambda particle: particle["world_x"])
            upwind = min(shell_particles, key=lambda particle: particle["world_x"])
            downwind_emission = max(emission_particles, key=lambda particle: particle["world_x"])
            upwind_emission = min(emission_particles, key=lambda particle: particle["world_x"])
            motion_context = particle_motion_context(project["scene"], particles)

            _downwind_world, downwind_release, _downwind_tail = animated_particle_position(
                downwind,
                project["scene"]["breakup"],
                0.78,
                motion_context=motion_context,
            )
            _upwind_world, upwind_release, _upwind_tail = animated_particle_position(
                upwind,
                project["scene"]["breakup"],
                0.78,
                motion_context=motion_context,
            )
            _downwind_emission_world, downwind_emission_release, _downwind_emission_tail = animated_particle_position(
                downwind_emission,
                project["scene"]["breakup"],
                0.78,
                motion_context=motion_context,
            )
            _upwind_emission_world, upwind_emission_release, _upwind_emission_tail = animated_particle_position(
                upwind_emission,
                project["scene"]["breakup"],
                0.78,
                motion_context=motion_context,
            )

            self.assertGreater(downwind_release, upwind_release * 1.2)
            self.assertGreater(downwind_emission_release, upwind_emission_release * 1.1)

    def test_emission_particles_travel_farther_than_shell_anchors_and_extend_plume(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_model = self._write_cube_obj(root)
            args = self._init_args(root, None, behavior="A shuttle model dissolves into monochrome particles.")
            init_project_bundle(args)
            project_path = Path(args.project)
            upload_project_model_source(project_path, self._model_upload_payload(raw_model, label="Shuttle Mesh"))
            apply_project_patch(
                project_path,
                {
                    "scene": {
                        "preset_family": "collision",
                        "breakup": {"amount": 0.62, "tail": 0.72, "drift_x": -0.48, "drift_y": -0.06, "retain": 0.66},
                    }
                },
            )

            project = load_project(project_path)
            particles = generate_active_particle_specs(project_path, project)
            motion_context = particle_motion_context(project["scene"], particles)
            shell_particles = [particle for particle in particles if particle["layer"] == "shell"][:280]
            emission_particles = [particle for particle in particles if particle["layer"] == "emission"][:280]

            self.assertTrue(all(particle["motion_mode"] == PARTICLE_MOTION_ANCHOR_SHELL for particle in shell_particles))
            self.assertTrue(all(particle["motion_mode"] == PARTICLE_MOTION_EMISSION_PLUME for particle in emission_particles))

            def average_displacement(group: list[dict[str, float]], progress: float) -> float:
                distances = []
                for particle in group:
                    world, _release, _tail = animated_particle_position(
                        particle,
                        project["scene"]["breakup"],
                        progress,
                        motion_context=motion_context,
                    )
                    dx = world[0] - particle["world_x"]
                    dy = world[1] - particle["world_y"]
                    dz = world[2] - particle["world_z"]
                    distances.append((dx * dx + dy * dy + dz * dz) ** 0.5)
                return sum(distances) / max(len(distances), 1)

            shell_displacement = average_displacement(shell_particles, 0.65)
            emission_displacement = average_displacement(emission_particles, 0.65)

            drift_direction = motion_context["drift_direction"]
            base_extent = max(
                (particle["world_x"] * drift_direction[0]) + (particle["world_y"] * drift_direction[1]) + (particle["world_z"] * drift_direction[2])
                for particle in particles
            )
            animated_extent = max(
                sum(component * direction for component, direction in zip(
                    animated_particle_position(
                        particle,
                        project["scene"]["breakup"],
                        0.65,
                        motion_context=motion_context,
                    )[0],
                    drift_direction,
                ))
                for particle in emission_particles
            )

            self.assertLess(shell_displacement, 0.03)
            self.assertGreater(emission_displacement, 0.12)
            self.assertGreater(emission_displacement, shell_displacement * 6.0)
            self.assertGreater(animated_extent, base_extent + 0.12)

    def test_plume_emission_envelope_moves_outward_from_source(self) -> None:
        early = plume_emission_envelope(0.0, 0.0, 0.0, 0.0)
        mid = plume_emission_envelope(0.35, 0.0, 0.0, 0.0)
        late = plume_emission_envelope(0.7, 0.0, 0.0, 0.0)

        self.assertLess(early, mid)
        self.assertLess(mid, late)

    def test_clear_model_source_returns_to_acquired_shell(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_image = self._write_isolated_source_image(root)
            raw_model = self._write_cube_obj(root)
            args = self._init_args(root, source_image)
            init_project_bundle(args)
            project_path = Path(args.project)
            select_project_model_source(
                project_path,
                {
                    "candidate": {
                        "query": "face",
                        "provider": "sketchfab",
                        "provider_label": "Sketchfab",
                        "remote_id": "face-cc0",
                        "remote_url": "https://sketchfab.com/3d-models/face-cc0",
                        "title": "Face Scan",
                        "license_class": "cc0",
                        "license_summary": "CC0",
                        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
                        "author_name": "Artist One",
                        "author_url": "https://sketchfab.com/artist-one",
                        "attribution_text": "Face Scan by Artist One via Sketchfab (CC0)",
                        "status": "fetched",
                        "raw_asset_path": str(raw_model),
                        "source_format": "obj",
                        "requires_auth": True,
                    }
                },
            )

            cleared = clear_project_model_source(project_path)

            self.assertEqual(cleared["scene"]["volume_backend"], VOLUME_BACKEND_ACQUIRED_SHELL)
            self.assertNotEqual(cleared["model_source"]["status"], MODEL_SOURCE_STATUS_SELECTED)

    def test_new_projects_default_to_volumetric_shell_model(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_image = self._write_isolated_source_image(root)
            args = self._init_args(root, source_image)

            init_project_bundle(args)
            loaded = load_project(Path(args.project))

            self.assertEqual(loaded["scene"]["effect_model"], DEFAULT_EFFECT_MODEL)
            self.assertEqual(loaded["scene"]["preset_family"], DEFAULT_PRESET_ID)
            self.assertEqual(loaded["scene"]["volume_backend"], VOLUME_BACKEND_ACQUIRED_SHELL)
            self.assertEqual(loaded["active_preset_id"], DEFAULT_PRESET_ID)
            self.assertEqual(loaded["saved_presets"], [])
            self.assertEqual(list(loaded["available_presets"].keys()), [DEFAULT_PRESET_ID])
            self.assertEqual(loaded["snapshots"][0]["kind"], "initial")
            self.assertEqual(loaded["snapshots"][0]["preset_id"], DEFAULT_PRESET_ID)
            self.assertGreater(loaded["scene"]["volume"]["depth_scale"], 0.4)
            self.assertGreater(loaded["scene"]["volume"]["depth_curve"], 1.0)
            self.assertLess(loaded["scene"]["volume"]["thickness_jitter"], 0.3)

    def test_load_project_migrates_legacy_builtin_preset_to_saved_preset_without_changing_effect(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_image = self._write_isolated_source_image(root)
            args = self._init_args(root, source_image, preset="memory")
            init_project_bundle(args)
            project_path = Path(args.project)
            raw_project = json.loads(project_path.read_text(encoding="utf-8"))

            loaded = load_project(project_path)

            self.assertEqual(loaded["scene"]["preset_family"], DEFAULT_PRESET_ID)
            self.assertNotEqual(loaded["active_preset_id"], DEFAULT_PRESET_ID)
            self.assertEqual(len(loaded["saved_presets"]), 1)
            self.assertEqual(loaded["saved_presets"][0]["label"], PRESET_DEFAULTS["memory"]["label"])
            self.assertAlmostEqual(loaded["scene"]["surface"]["density"], raw_project["scene"]["surface"]["density"], places=3)
            self.assertAlmostEqual(loaded["scene"]["breakup"]["amount"], raw_project["scene"]["breakup"]["amount"], places=3)
            self.assertAlmostEqual(loaded["saved_presets"][0]["effect"]["surface"]["density"], raw_project["scene"]["surface"]["density"], places=3)
            self.assertAlmostEqual(loaded["saved_presets"][0]["effect"]["breakup"]["amount"], raw_project["scene"]["breakup"]["amount"], places=3)

    def test_load_project_migrates_legacy_effect_model_with_backup_then_reset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_image = self._write_isolated_source_image(root)
            args = self._init_args(root, source_image)
            init_project_bundle(args)
            project_path = Path(args.project)

            raw_project = json.loads(project_path.read_text(encoding="utf-8"))
            raw_project["scene"]["effect_model"] = "volumetric_shell_v1"
            raw_project["scene"]["surface"]["opacity"] = 0.13
            raw_project["scene"]["camera"]["yaw"] = 1.22
            raw_project["scene"]["volume"] = {
                "depth_scale": 0.38,
                "depth_curve": 1.05,
                "thickness_jitter": 0.26,
            }
            project_path.write_text(json.dumps(raw_project, indent=2) + "\n", encoding="utf-8")

            migrated = load_project(project_path)
            migrated_again = load_project(project_path)

            backup_snapshots = [snapshot for snapshot in migrated_again["snapshots"] if snapshot["label"] == f"Auto backup before {DEFAULT_EFFECT_MODEL}"]
            self.assertEqual(migrated["scene"]["effect_model"], DEFAULT_EFFECT_MODEL)
            self.assertAlmostEqual(migrated["scene"]["surface"]["opacity"], PRESET_DEFAULTS[DEFAULT_PRESET_ID]["surface"]["opacity"], places=2)
            self.assertNotAlmostEqual(migrated["scene"]["camera"]["yaw"], 1.22, places=2)
            self.assertEqual(len(backup_snapshots), 1)
            self.assertEqual(backup_snapshots[0]["scene"]["effect_model"], "volumetric_shell_v1")
            self.assertAlmostEqual(backup_snapshots[0]["scene"]["surface"]["opacity"], 0.13, places=2)

    def test_legacy_shell_volume_triplet_upgrades_to_current_preset_baseline(self) -> None:
        scene = resolve_preset_scene(
            {
                "effect_model": DEFAULT_EFFECT_MODEL,
                "preset_family": "vigil",
                "volume": {
                    "depth_scale": 0.38,
                    "depth_curve": 1.05,
                    "thickness_jitter": 0.26,
                },
            },
            "vigil",
        )

        self.assertAlmostEqual(scene["volume"]["depth_scale"], 0.58, places=3)
        self.assertAlmostEqual(scene["volume"]["depth_curve"], 1.22, places=3)
        self.assertAlmostEqual(scene["volume"]["thickness_jitter"], 0.12, places=3)

    def test_shell_generator_biases_particles_to_surface_with_depth_spread(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_image = self._write_isolated_source_image(root)
            args = self._init_args(root, source_image)

            init_project_bundle(args)
            _project, particles = self._particles_for_project(Path(args.project))

            shell_count = sum(1 for particle in particles if particle["layer"] == "shell")
            attachment_count = sum(1 for particle in particles if particle["layer"] == "attachment")
            halo_count = sum(1 for particle in particles if particle["layer"] == "halo")
            z_values = [particle["world_z"] for particle in particles]

            self.assertGreater(shell_count, attachment_count)
            self.assertGreater(shell_count, halo_count)
            self.assertGreater(max(z_values) - min(z_values), 0.35)

    def test_load_project_rejects_malformed_json_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "project.json"
            project_path.write_text("{ invalid }\n", encoding="utf-8")

            with self.assertRaises(WorkbenchError):
                load_project(project_path)

    def test_shell_particles_remain_stable_across_preview_loop(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_image = self._write_isolated_source_image(root)
            args = self._init_args(root, source_image)

            init_project_bundle(args)
            project, particles = self._particles_for_project(Path(args.project))
            shell_particles = [particle for particle in particles if particle["layer"] == "shell"][:240]

            def average_displacement(progress: float) -> float:
                distances = []
                for particle in shell_particles:
                    world, _release, _tail = animated_particle_position(particle, project["scene"]["breakup"], progress)
                    dx = world[0] - particle["world_x"]
                    dy = world[1] - particle["world_y"]
                    dz = world[2] - particle["world_z"]
                    distances.append((dx * dx + dy * dy + dz * dz) ** 0.5)
                return sum(distances) / max(len(distances), 1)

            early = average_displacement(0.12)
            middle = average_displacement(0.50)
            late = average_displacement(0.88)

            self.assertLess(early, 0.04)
            self.assertLess(middle, 0.04)
            self.assertLess(late, 0.04)
            self.assertLess(abs(late - early), 0.04)

    def test_emitter_controls_materially_change_plume_response(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_model = self._write_cube_obj(root)
            args = self._init_args(root, None, behavior="A shuttle model dissolves into monochrome particles.")
            init_project_bundle(args)
            project_path = Path(args.project)
            upload_project_model_source(project_path, self._model_upload_payload(raw_model, label="Shuttle Mesh"))
            apply_project_patch(
                project_path,
                {
                    "scene": {
                        "preset_family": "collision",
                        "breakup": {"amount": 0.62, "tail": 0.72, "drift_x": -0.48, "drift_y": -0.06, "retain": 0.66},
                    }
                },
            )

            def plume_metrics(emitter_patch: dict[str, float]) -> tuple[float, float, float]:
                apply_project_patch(project_path, {"scene": {"emitter": emitter_patch}})
                project = load_project(project_path)
                particles = generate_active_particle_specs(project_path, project)
                motion_context = particle_motion_context(project["scene"], particles)
                emission_particles = [particle for particle in particles if particle["layer"] == "emission"][:280]
                displacements = []
                releases = []
                tails = []
                for particle in emission_particles:
                    world, release, tail = animated_particle_position(
                        particle,
                        project["scene"]["breakup"],
                        0.68,
                        motion_context=motion_context,
                    )
                    dx = world[0] - particle["world_x"]
                    dy = world[1] - particle["world_y"]
                    dz = world[2] - particle["world_z"]
                    displacements.append((dx * dx + dy * dy + dz * dz) ** 0.5)
                    releases.append(release)
                    tails.append(tail)
                return (
                    sum(displacements) / max(len(displacements), 1),
                    sum(releases) / max(len(releases), 1),
                    sum(tails) / max(len(tails), 1),
                )

            baseline_displacement, baseline_release, baseline_tail = plume_metrics({"strength": 0.18, "rate": 0.18, "decay": 0.18})
            strong_displacement, strong_release, strong_tail = plume_metrics({"strength": 1.25, "rate": 1.25, "decay": 0.18})
            _short_displacement, _short_release, short_tail = plume_metrics({"strength": 1.25, "rate": 1.25, "decay": 0.95})

            self.assertGreater(strong_displacement, baseline_displacement * 1.8)
            self.assertGreater(strong_release, baseline_release * 1.8)
            self.assertGreater(strong_tail, baseline_tail * 2.0)
            self.assertLess(short_tail, strong_tail * 0.8)

    def test_subject_relative_model_emitter_direction_is_stable_across_camera_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            args = self._init_args(root, None, behavior="A shuttle orbiter dissolves into monochrome particles.")
            init_project_bundle(args)
            project_path = Path(args.project)

            apply_project_patch(
                project_path,
                {
                    "scene": {
                        "emitter": {
                            "direction_x": 0.31,
                            "direction_y": 0.82,
                            "direction_z": -0.47,
                        }
                    }
                },
            )
            project = load_project(project_path)
            particles = generate_active_particle_specs(project_path, project)
            motion_a = particle_motion_context(project["scene"], particles)

            shifted_scene = copy.deepcopy(project["scene"])
            shifted_scene["camera"] = {
                **shifted_scene["camera"],
                "yaw": float(shifted_scene["camera"]["yaw"]) + 0.74,
                "pitch": float(shifted_scene["camera"]["pitch"]) - 0.18,
            }
            motion_b = particle_motion_context(shifted_scene, particles)

            self.assertEqual(project["scene"]["emitter"]["direction_space"], "subject")
            self.assertEqual(motion_a["direction_space"], "subject")
            self.assertAlmostEqual(motion_a["drift_direction"][0], motion_b["drift_direction"][0], places=5)
            self.assertAlmostEqual(motion_a["drift_direction"][1], motion_b["drift_direction"][1], places=5)
            self.assertAlmostEqual(motion_a["drift_direction"][2], motion_b["drift_direction"][2], places=5)

    def test_preview_render_changes_when_camera_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_image = self._write_isolated_source_image(root)
            args = self._init_args(root, source_image)
            init_project_bundle(args)
            project_path = Path(args.project)

            preview_a = render_preview_png(project_path, load_project(project_path), 0.55)
            apply_project_patch(
                project_path,
                {
                    "scene": {
                        "camera": {"yaw": 1.02, "pitch": 0.28, "distance": 2.05},
                    }
                },
            )
            preview_b = render_preview_png(project_path, load_project(project_path), 0.55)

            self.assertNotEqual(preview_a, preview_b)

    def test_non_model_scene_keeps_camera_relative_emitter_space(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_image = self._write_isolated_source_image(root)
            args = self._init_args(root, source_image)

            init_project_bundle(args)
            project = load_project(Path(args.project))

            self.assertEqual(project["scene"]["volume_backend"], VOLUME_BACKEND_ACQUIRED_SHELL)
            self.assertEqual(project["scene"]["emitter"]["direction_space"], "camera")

    def test_legacy_default_model_emitter_upgrades_to_subject_space(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            args = self._init_args(root, None, behavior="A shuttle orbiter dissolves into monochrome particles.")
            init_project_bundle(args)
            project_path = Path(args.project)

            raw_project = json.loads(project_path.read_text(encoding="utf-8"))
            legacy_defaults = emitter_defaults(breakup=raw_project["scene"]["breakup"])
            raw_project["scene"]["emitter"].pop("direction_space", None)
            raw_project["scene"]["emitter"]["direction_x"] = legacy_defaults["direction_x"]
            raw_project["scene"]["emitter"]["direction_y"] = legacy_defaults["direction_y"]
            raw_project["scene"]["emitter"]["direction_z"] = legacy_defaults["direction_z"]
            raw_project["scene"]["emitter"]["strength"] = 1.11
            project_path.write_text(json.dumps(raw_project, indent=2) + "\n", encoding="utf-8")

            migrated = load_project(project_path)

            self.assertEqual(migrated["scene"]["emitter"]["direction_space"], "subject")
            self.assertAlmostEqual(migrated["scene"]["emitter"]["strength"], 1.11, places=2)
            self.assertNotAlmostEqual(migrated["scene"]["emitter"]["direction_x"], legacy_defaults["direction_x"], places=2)

    def test_legacy_custom_model_emitter_stays_camera_relative(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            args = self._init_args(root, None, behavior="A shuttle orbiter dissolves into monochrome particles.")
            init_project_bundle(args)
            project_path = Path(args.project)

            raw_project = json.loads(project_path.read_text(encoding="utf-8"))
            raw_project["scene"]["emitter"].pop("direction_space", None)
            raw_project["scene"]["emitter"]["direction_x"] = 0.61
            raw_project["scene"]["emitter"]["direction_y"] = -0.22
            raw_project["scene"]["emitter"]["direction_z"] = 0.73
            project_path.write_text(json.dumps(raw_project, indent=2) + "\n", encoding="utf-8")

            migrated = load_project(project_path)

            self.assertEqual(migrated["scene"]["emitter"]["direction_space"], "camera")
            self.assertAlmostEqual(migrated["scene"]["emitter"]["direction_x"], 0.61, places=3)
            self.assertAlmostEqual(migrated["scene"]["emitter"]["direction_y"], -0.22, places=3)
            self.assertAlmostEqual(migrated["scene"]["emitter"]["direction_z"], 0.73, places=3)

    def test_export_project_shot_supports_model_source_backend(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_image = self._write_isolated_source_image(root)
            raw_model = self._write_cube_obj(root)
            init_args = self._init_args(root, source_image)
            init_project_bundle(init_args)
            project_path = Path(init_args.project)
            select_project_model_source(
                project_path,
                {
                    "candidate": {
                        "query": "face",
                        "provider": "sketchfab",
                        "provider_label": "Sketchfab",
                        "remote_id": "face-cc0",
                        "remote_url": "https://sketchfab.com/3d-models/face-cc0",
                        "title": "Face Scan",
                        "license_class": "cc0",
                        "license_summary": "CC0",
                        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
                        "author_name": "Artist One",
                        "author_url": "https://sketchfab.com/artist-one",
                        "attribution_text": "Face Scan by Artist One via Sketchfab (CC0)",
                        "status": "fetched",
                        "raw_asset_path": str(raw_model),
                        "source_format": "obj",
                        "requires_auth": True,
                    }
                },
            )

            export_args = Namespace(
                project=init_args.project,
                output=str(root / "exports" / "model-proof.mp4"),
                manifest_output=None,
                poster_output=None,
                still_output=None,
                snapshot_id="snapshot_initial",
                width=None,
                height=None,
                frames=24,
                fps=24,
                min_duration_seconds=1.0,
                command="export-shot",
                repo_root=str(ROOT),
            )

            with mock.patch("workbench_tool.serve_export_session", new=self._fake_export_session()), mock.patch(
                "workbench_tool.export_frames_with_webgl",
                side_effect=self._fake_webgl_export(),
            ), mock.patch("workbench_tool.encode_frames_to_video", side_effect=self._fake_primary_encode()), mock.patch(
                "workbench_tool.encode_frames_to_lossless_master_video",
                side_effect=self._fake_master_encode(),
            ):
                manifest = export_project_shot(export_args)

            self.assertEqual(manifest["volume_backend"], VOLUME_BACKEND_MODEL_SOURCE)
            self.assertEqual(manifest["model_source"]["provider"], "sketchfab")
            self.assertEqual(manifest["model_source"]["author_name"], "Artist One")
            self.assertEqual(manifest["model_source"]["license_url"], "https://creativecommons.org/publicdomain/zero/1.0/")
            self.assertIn("Sketchfab", manifest["model_source"]["attribution_text"])
            self.assertTrue(Path(manifest["poster_path"]).exists())
            self.assertTrue(Path(manifest["master_output_path"]).exists())
            self.assertEqual(Path(manifest["master_output_path"]).suffix, ".mkv")
            self.assertTrue(manifest["master_lossless"])

    def test_export_project_shot_uses_current_draft_scene_for_snapshot_initial(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_model = self._write_cube_obj(root)
            init_args = self._init_args(root, None, behavior="A shuttle model dissolves into monochrome particles.")
            init_args.min_duration_seconds = 3.0
            init_project_bundle(init_args)
            project_path = Path(init_args.project)
            upload_project_model_source(project_path, self._model_upload_payload(raw_model, label="Shuttle Mesh"))
            apply_project_patch(
                project_path,
                {
                    "scene": {
                        "preset_family": "collision",
                        "breakup": {"amount": 0.62, "retain": 0.66},
                    }
                },
            )

            export_args = Namespace(
                project=init_args.project,
                output=str(root / "exports" / "model-draft-proof.mp4"),
                manifest_output=None,
                poster_output=None,
                still_output=None,
                snapshot_id="snapshot_initial",
                width=None,
                height=None,
                frames=24,
                fps=24,
                min_duration_seconds=1.0,
                command="export-shot",
                repo_root=str(ROOT),
            )

            with mock.patch("workbench_tool.serve_export_session", new=self._fake_export_session()), mock.patch(
                "workbench_tool.export_frames_with_webgl",
                side_effect=self._fake_webgl_export(),
            ), mock.patch("workbench_tool.encode_frames_to_video", side_effect=self._fake_primary_encode()), mock.patch(
                "workbench_tool.encode_frames_to_lossless_master_video",
                side_effect=self._fake_master_encode(),
            ):
                manifest = export_project_shot(export_args)

            self.assertEqual(manifest["preset_family"], DEFAULT_PRESET_ID)
            self.assertEqual(manifest["approval"]["status"], "draft")

    def test_export_project_shot_uses_requested_approved_snapshot_not_current_draft_scene(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_model = self._write_cube_obj(root)
            init_args = self._init_args(root, None, behavior="A shuttle model dissolves into monochrome particles.")
            init_args.min_duration_seconds = 3.0
            init_project_bundle(init_args)
            project_path = Path(init_args.project)
            upload_project_model_source(project_path, self._model_upload_payload(raw_model, label="Shuttle Mesh"))
            apply_project_patch(
                project_path,
                {
                    "scene": {
                        "preset_family": "vigil",
                        "breakup": {"amount": 0.03, "retain": 0.0},
                    }
                },
            )
            approved_project = approve_project_look(project_path)
            approved_snapshot_id = approved_project["approval"]["snapshot_id"]
            apply_project_patch(
                project_path,
                {
                    "scene": {
                        "preset_family": "collision",
                        "breakup": {"amount": 0.62, "retain": 0.66},
                    }
                },
            )

            captured_sessions: list[dict[str, object]] = []

            export_args = Namespace(
                project=init_args.project,
                output=str(root / "exports" / "approved-proof.mp4"),
                manifest_output=None,
                poster_output=None,
                still_output=None,
                snapshot_id=approved_snapshot_id,
                width=3840,
                height=2160,
                frames=180,
                fps=60,
                min_duration_seconds=3.0,
                command="export-shot",
                repo_root=str(ROOT),
            )

            with mock.patch("workbench_tool.serve_export_session", new=self._fake_export_session(captured_sessions)), mock.patch(
                "workbench_tool.export_frames_with_webgl",
                side_effect=self._fake_webgl_export(),
            ), mock.patch("workbench_tool.encode_frames_to_video", side_effect=self._fake_primary_encode()), mock.patch(
                "workbench_tool.encode_frames_to_lossless_master_video",
                side_effect=self._fake_master_encode(),
            ):
                manifest = export_project_shot(export_args)

            self.assertEqual(manifest["snapshot_id"], approved_snapshot_id)
            self.assertEqual(manifest["preset_family"], DEFAULT_PRESET_ID)
            self.assertEqual(manifest["width"], 3840)
            self.assertEqual(manifest["height"], 2160)
            self.assertEqual(manifest["fps"], 60)
            self.assertEqual(manifest["rendered_frames"], 180)
            self.assertEqual(captured_sessions[0]["project"]["scene"]["preset_family"], DEFAULT_PRESET_ID)
            self.assertEqual(captured_sessions[0]["project"]["motion_contract"]["width"], 3840)
            self.assertEqual(captured_sessions[0]["project"]["motion_contract"]["height"], 2160)
            self.assertEqual(captured_sessions[0]["project"]["motion_contract"]["fps"], 60)
            self.assertEqual(captured_sessions[0]["project"]["motion_contract"]["frames"], 180)
            self.assertEqual(captured_sessions[0]["project"]["scene"]["shot"]["fps"], 60)
            self.assertEqual(captured_sessions[0]["project"]["scene"]["shot"]["frames"], 180)
            self.assertEqual(captured_sessions[0]["project"]["scene"]["shot"]["duration_seconds"], 3.0)
            self.assertEqual(load_project(project_path)["scene"]["preset_family"], DEFAULT_PRESET_ID)

    def test_select_project_snapshot_restores_scene_and_preserves_approved_snapshot_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_model = self._write_cube_obj(root)
            init_args = self._init_args(root, None, behavior="A shuttle model dissolves into monochrome particles.")
            init_project_bundle(init_args)
            project_path = Path(init_args.project)
            upload_project_model_source(project_path, self._model_upload_payload(raw_model, label="Shuttle Mesh"))

            apply_project_patch(
                project_path,
                {
                    "scene": {
                        "camera": {"yaw": 0.77, "pitch": 0.21},
                        "surface": {"density": 1.25},
                    }
                },
            )
            manual_snapshot = workbench_tool_module.append_snapshot(project_path, "Manual snapshot")
            manual_snapshot_id = manual_snapshot["active_snapshot_id"]

            approved = approve_project_look(project_path)
            approved_snapshot_id = approved["approval"]["snapshot_id"]

            apply_project_patch(
                project_path,
                {
                    "scene": {
                        "camera": {"yaw": 0.22, "pitch": 0.08},
                        "surface": {"density": 0.48},
                    }
                },
            )

            restored_manual = select_project_snapshot(project_path, manual_snapshot_id)
            restored_approved = select_project_snapshot(project_path, approved_snapshot_id)

            self.assertEqual(restored_manual["active_snapshot_id"], manual_snapshot_id)
            self.assertEqual(restored_manual["approval"]["status"], "draft")
            self.assertAlmostEqual(restored_manual["scene"]["camera"]["yaw"], 0.77, places=2)
            self.assertAlmostEqual(restored_manual["scene"]["surface"]["density"], 1.25, places=3)
            self.assertEqual(restored_manual["snapshots"][1]["kind"], "snapshot")

            self.assertEqual(restored_approved["active_snapshot_id"], approved_snapshot_id)
            self.assertEqual(restored_approved["approval"]["status"], "approved")
            self.assertAlmostEqual(restored_approved["scene"]["surface"]["density"], 1.25, places=3)
            self.assertEqual(restored_approved["snapshots"][2]["kind"], "approved")

    def test_load_project_migrates_snapshot_kind_and_preset_metadata_for_legacy_records(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_model = self._write_cube_obj(root)
            init_args = self._init_args(root, None, behavior="A shuttle model dissolves into monochrome particles.")
            init_project_bundle(init_args)
            project_path = Path(init_args.project)
            upload_project_model_source(project_path, self._model_upload_payload(raw_model, label="Shuttle Mesh"))
            workbench_tool_module.append_snapshot(project_path, "Manual snapshot")
            approved = approve_project_look(project_path)
            approved_snapshot_id = approved["approval"]["snapshot_id"]

            raw_project = json.loads(project_path.read_text(encoding="utf-8"))
            raw_project.pop("active_preset_id", None)
            raw_project.pop("saved_presets", None)
            for snapshot in raw_project["snapshots"]:
                snapshot.pop("kind", None)
                snapshot.pop("preset_id", None)
            project_path.write_text(json.dumps(raw_project, indent=2), encoding="utf-8")

            loaded = load_project(project_path)
            snapshots_by_id = {snapshot["id"]: snapshot for snapshot in loaded["snapshots"]}

            self.assertEqual(snapshots_by_id["snapshot_initial"]["kind"], "initial")
            self.assertEqual(snapshots_by_id["snapshot_initial"]["preset_id"], DEFAULT_PRESET_ID)
            self.assertEqual(snapshots_by_id["snapshot_02"]["kind"], "snapshot")
            self.assertEqual(snapshots_by_id[approved_snapshot_id]["kind"], "approved")
            self.assertEqual(snapshots_by_id[approved_snapshot_id]["preset_id"], DEFAULT_PRESET_ID)

    def test_burn_project_video_requires_approval_for_model_only_flow(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_model = self._write_cube_obj(root)
            init_args = self._init_args(root, None, behavior="A shuttle model breaks into particles.")
            init_project_bundle(init_args)
            project_path = Path(init_args.project)
            upload_project_model_source(project_path, self._model_upload_payload(raw_model, label="Shuttle Mesh"))

            with self.assertRaises(WorkbenchError):
                burn_project_video(project_path, {})

            approve_project_look(project_path)

            with mock.patch("workbench_tool.serve_export_session", new=self._fake_export_session()), mock.patch(
                "workbench_tool.export_frames_with_webgl",
                side_effect=self._fake_webgl_export(),
            ), mock.patch("workbench_tool.encode_frames_to_video", side_effect=self._fake_primary_encode()), mock.patch(
                "workbench_tool.encode_frames_to_lossless_master_video",
                side_effect=self._fake_master_encode(),
            ):
                manifest = burn_project_video(project_path, {})

            burned_project = load_project(project_path)
            self.assertEqual(manifest["volume_backend"], VOLUME_BACKEND_MODEL_SOURCE)
            self.assertEqual(manifest["model_source"]["provider"], "local_upload")
            self.assertEqual(manifest["approval"]["status"], "approved")
            self.assertTrue(Path(manifest["output_path"]).exists())
            self.assertTrue(Path(manifest["master_output_path"]).exists())
            self.assertTrue(Path(manifest["poster_path"]).exists())
            self.assertTrue(Path(manifest["still_path"]).exists())
            self.assertEqual(burned_project["approval"]["output_path"], manifest["output_path"])
            self.assertEqual(burned_project["approval"]["master_output_path"], manifest["master_output_path"])
            self.assertEqual(burned_project["approval"]["master_codec"], "ffv1")
            self.assertEqual(burned_project["approval"]["master_container"], "mkv")
            self.assertTrue(burned_project["approval"]["master_lossless"])
            self.assertEqual(burned_project["approval"]["manifest_path"], manifest["manifest_path"])
            self.assertEqual(burned_project["approval"]["poster_path"], manifest["poster_path"])
            self.assertEqual(burned_project["approval"]["still_path"], manifest["still_path"])

    def test_export_project_shot_uses_only_approved_mask(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_image = self._write_scenic_source_image(root)
            mask_image = self._write_mask_image(root)
            init_args = self._init_args(root, source_image, mask_image=mask_image)
            init_project_bundle(init_args)

            export_args = Namespace(
                project=init_args.project,
                output=str(root / "exports" / "proof.mp4"),
                manifest_output=None,
                poster_output=None,
                still_output=None,
                snapshot_id="snapshot_initial",
                width=None,
                height=None,
                frames=None,
                fps=None,
                min_duration_seconds=None,
                command="export-shot",
                repo_root=str(ROOT),
            )

            with mock.patch("workbench_tool.serve_export_session", new=self._fake_export_session()), mock.patch(
                "workbench_tool.export_frames_with_webgl",
                side_effect=self._fake_webgl_export(),
            ), mock.patch("workbench_tool.encode_frames_to_video", side_effect=self._fake_primary_encode()), mock.patch(
                "workbench_tool.encode_frames_to_lossless_master_video",
                side_effect=self._fake_master_encode(),
            ):
                manifest = export_project_shot(export_args)

            poster_path = Path(manifest["poster_path"])
            self.assertEqual(manifest["mask_source"], "imported")
            self.assertTrue(manifest["mask_sha256"])
            self.assertEqual(manifest["source_id"], "source_01")
            self.assertEqual(manifest["effect_model"], DEFAULT_EFFECT_MODEL)
            with Image.open(poster_path) as poster:
                grayscale = poster.convert("L")
                stats = ImageStat.Stat(grayscale)
                self.assertLess(stats.mean[0], 80.0)
                left_strip = grayscale.crop((0, 0, grayscale.width // 4, grayscale.height))
                self.assertLess(ImageStat.Stat(left_strip).mean[0], 30.0)

    def test_export_project_shot_records_active_prior_assist_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_image = self._write_shuttle_stack_source_image(root)
            init_args = self._init_args(
                root,
                source_image,
                behavior="The space shuttle orbiter dissolves into monochrome particles.",
            )
            init_project_bundle(init_args)

            export_args = Namespace(
                project=init_args.project,
                output=str(root / "exports" / "prior-assist-proof.mp4"),
                manifest_output=None,
                poster_output=None,
                still_output=None,
                snapshot_id="snapshot_initial",
                width=None,
                height=None,
                frames=24,
                fps=24,
                min_duration_seconds=1.0,
                command="export-shot",
                repo_root=str(ROOT),
            )

            with mock.patch("workbench_tool.serve_export_session", new=self._fake_export_session()), mock.patch(
                "workbench_tool.export_frames_with_webgl",
                side_effect=self._fake_webgl_export(),
            ), mock.patch("workbench_tool.encode_frames_to_video", side_effect=self._fake_primary_encode()), mock.patch(
                "workbench_tool.encode_frames_to_lossless_master_video",
                side_effect=self._fake_master_encode(),
            ):
                manifest = export_project_shot(export_args)

            self.assertEqual(manifest["volume_backend"], VOLUME_BACKEND_ACQUIRED_SHELL)
            self.assertEqual(manifest["prior_assist"]["status"], PRIOR_ASSIST_STATUS_ACTIVE)
            self.assertTrue(manifest["prior_assist"]["prior_id"].startswith("space_shuttle_"))

    def test_poly_pizza_search_filters_to_cc0_results(self) -> None:
        bootstrap = {
            "initialData": {
                "result": [
                    {
                        "publicID": "cc0_ship",
                        "url": "/m/cc0_ship",
                        "title": "CC0 Ship",
                        "previewUrl": "https://static.poly.pizza/cc0.webp",
                        "licence": "CC0 1.0",
                    },
                    {
                        "publicID": "by_ship",
                        "url": "/m/by_ship",
                        "title": "BY Ship",
                        "previewUrl": "https://static.poly.pizza/by.webp",
                        "licence": "CC-BY 3.0",
                    },
                ]
            }
        }
        html = f"<script>window.__BOOTSTRAP__ = {json.dumps(bootstrap)};var a=1;</script>"

        with mock.patch("workbench_model_source._fetch_text", return_value=html):
            results = search_poly_pizza("ship")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["remote_id"], "cc0_ship")
        self.assertEqual(results[0]["preview_url"], "https://static.poly.pizza/cc0.webp")

    def test_search_model_candidates_attaches_provider_policy_metadata(self) -> None:
        with mock.patch(
            "workbench_model_source.search_poly_pizza",
            return_value=[
                {
                    "provider": "poly_pizza",
                    "provider_label": "Poly Pizza",
                    "remote_id": "cc0_ship",
                    "remote_url": "https://poly.pizza/m/cc0_ship",
                    "title": "CC0 Ship",
                    "license_class": "cc0",
                    "status": "search_result",
                    "match_score": 0.7,
                }
            ],
        ), mock.patch(
            "workbench_model_source.search_nasa",
            return_value=[
                {
                    "provider": "nasa_3d",
                    "provider_label": "NASA 3D",
                    "remote_id": "shuttle",
                    "remote_url": "https://science.nasa.gov/3d-resources/shuttle/",
                    "title": "Space Shuttle",
                    "license_class": "nasa_media_guidelines",
                    "status": "search_result",
                    "match_score": 0.9,
                }
            ],
        ), mock.patch(
            "workbench_model_source.search_smithsonian",
            return_value=[
                {
                    "provider": "smithsonian_open_access",
                    "provider_label": "Smithsonian OA",
                    "remote_id": "smithsonian_shuttle",
                    "remote_url": "https://3d.si.edu/object/3d/example",
                    "title": "Shuttle Artifact",
                    "license_class": "candidate",
                    "status": "search_result",
                    "match_score": 0.5,
                }
            ],
        ), mock.patch(
            "workbench_model_source.search_sketchfab",
            return_value=[
                {
                    "provider": "sketchfab",
                    "provider_label": "Sketchfab",
                    "remote_id": "head-model",
                    "remote_url": "https://sketchfab.com/3d-models/head-model",
                    "title": "Head Model",
                    "license_class": "by",
                    "license_summary": "CC BY",
                    "license_url": "https://creativecommons.org/licenses/by/4.0/",
                    "author_name": "Model Author",
                    "author_url": "https://sketchfab.com/model-author",
                    "requires_auth": True,
                    "status": "search_result",
                    "match_score": 0.8,
                }
            ],
        ):
            results = search_model_candidates("shuttle")

        by_provider = {result["provider"]: result for result in results}
        self.assertEqual(by_provider["nasa_3d"]["provider_kind"], "open_access")
        self.assertEqual(by_provider["nasa_3d"]["provider_capability"], "enabled")
        self.assertEqual(by_provider["nasa_3d"]["subject_fit"], "real_world")
        self.assertEqual(by_provider["poly_pizza"]["provider_kind"], "open_license")
        self.assertEqual(by_provider["poly_pizza"]["provider_capability"], "enabled")
        self.assertEqual(by_provider["poly_pizza"]["subject_fit"], "conditional")
        self.assertEqual(by_provider["sketchfab"]["provider_kind"], "open_license")
        self.assertEqual(by_provider["sketchfab"]["provider_capability"], "enabled")
        self.assertEqual(by_provider["sketchfab"]["license_summary"], "CC BY")
        self.assertTrue(by_provider["sketchfab"]["requires_auth"])
        self.assertEqual(by_provider["smithsonian_open_access"]["provider_capability"], "search_only")
        self.assertEqual(by_provider["smithsonian_open_access"]["license_summary"], "CC0 Open Access")
        self.assertIn("search-only", by_provider["smithsonian_open_access"]["eligibility_note"].lower())
        self.assertIn("provider_kind", by_provider["nasa_3d"]["provider_policy"])

    def test_search_sketchfab_only_returns_downloadable_open_license_models(self) -> None:
        payload = {
            "results": [
                {
                    "uid": "face-cc0",
                    "name": "Face Scan",
                    "viewerUrl": "https://sketchfab.com/3d-models/face-cc0",
                    "isDownloadable": True,
                    "license": {
                        "uid": "322a749bcfa841b29dff1e8a1bb74b0b",
                        "label": "CC Attribution",
                    },
                    "thumbnails": {"images": [{"url": "https://media.sketchfab.com/thumb.webp", "width": 512, "height": 512}]},
                    "user": {
                        "displayName": "Artist One",
                        "profileUrl": "https://sketchfab.com/artist-one",
                        "username": "artist_one",
                    },
                },
                {
                    "uid": "face-nc",
                    "name": "Restricted Face",
                    "viewerUrl": "https://sketchfab.com/3d-models/face-nc",
                    "isDownloadable": True,
                    "license": {
                        "uid": "bbfe3f7dbcdd4122b966b85b9786a989",
                        "label": "CC Attribution-NonCommercial",
                    },
                    "user": {"displayName": "Artist Two"},
                },
                {
                    "uid": "face-private",
                    "name": "Private Face",
                    "viewerUrl": "https://sketchfab.com/3d-models/face-private",
                    "isDownloadable": False,
                    "license": "cc0",
                    "user": {"displayName": "Artist Three"},
                },
            ]
        }

        with mock.patch("workbench_model_source._fetch_json", return_value=payload):
            results = search_sketchfab("face")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["remote_id"], "face-cc0")
        self.assertEqual(results[0]["license_summary"], "CC BY")
        self.assertEqual(results[0]["author_name"], "Artist One")
        self.assertTrue(results[0]["requires_auth"])

    def test_fetch_sketchfab_requires_auth_when_uncached(self) -> None:
        candidate = {
            "provider": "sketchfab",
            "remote_id": "face-cc0",
            "remote_url": "https://sketchfab.com/3d-models/face-cc0",
            "title": "Face Scan",
            "license_class": "cc0",
            "license_summary": "CC0",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ModelSourceError) as raised:
                fetch_sketchfab(candidate, Path(temp_dir), access_token=None)

        self.assertIn("personal api token", str(raised.exception).lower())

    def test_fetch_sketchfab_downloads_archive_and_collapses_to_glb(self) -> None:
        candidate = {
            "provider": "sketchfab",
            "remote_id": "face-cc0",
            "remote_url": "https://sketchfab.com/3d-models/face-cc0",
            "title": "Face Scan",
            "license_class": "cc0",
            "license_summary": "CC0",
            "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
            "author_name": "Artist One",
            "author_url": "https://sketchfab.com/artist-one",
        }
        archive_bytes = io.BytesIO()
        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(archive_bytes, "w") as archive:
                archive.writestr("scene.gltf", json.dumps({"asset": {"version": "2.0"}, "scenes": []}))
                archive.writestr("buffer.bin", b"1234")
            cache_root = Path(temp_dir)

            def fake_collapse(source_asset_path: Path, output_path: Path) -> Path:
                self.assertEqual(source_asset_path.name, "scene.gltf")
                output_path.write_bytes(b"glb-bytes")
                return output_path

            with mock.patch(
                "workbench_model_source._fetch_json",
                return_value={"gltf": {"url": "https://download.sketchfab.com/archive.zip", "expires": 300}},
            ) as fetch_json_mock, mock.patch(
                "workbench_model_source._fetch_url",
                return_value=archive_bytes.getvalue(),
            ), mock.patch(
                "workbench_model_source._collapse_sketchfab_asset_to_glb",
                side_effect=fake_collapse,
            ):
                fetched = fetch_sketchfab(candidate, cache_root, access_token="sketchfab-token")

            self.assertEqual(fetched["source_format"], "glb")
            self.assertTrue(Path(fetched["raw_asset_path"]).exists())
            self.assertEqual(Path(fetched["raw_asset_path"]).read_bytes(), b"glb-bytes")
            self.assertIn("Artist One", fetched["attribution_text"])
            self.assertEqual(fetch_json_mock.call_args.kwargs["headers"]["Authorization"], "Token sketchfab-token")

    def test_external_model_source_resources_build_site_scoped_search_urls(self) -> None:
        resources = external_model_source_resources("face")

        self.assertEqual(len(resources), 4)
        self.assertEqual(resources[0]["label"], "CGTrader")
        self.assertIn("face", resources[0]["search_url"])

    def test_sketchfab_auth_status_reports_no_token_when_disconnected(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "CE_SKETCHFAB_API_TOKEN": "",
            },
            clear=False,
        ):
            status = sketchfab_auth_status()

        self.assertFalse(status["configured"])
        self.assertFalse(status["connected"])
        self.assertEqual(status["token_source"], "none")
        self.assertIn("personal token", status["message"].lower())

    def test_connect_sketchfab_token_persists_private_cache_and_disconnect_clears_it(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.dict(
            os.environ,
            {
                "XDG_CACHE_HOME": temp_dir,
                "CE_SKETCHFAB_API_TOKEN": "",
            },
            clear=False,
        ):
            with mock.patch(
                "workbench_tool._sketchfab_profile_summary",
                return_value={
                    "uid": "user-1",
                    "username": "artist_one",
                    "display_name": "Artist One",
                    "profile_url": "https://sketchfab.com/artist-one",
                },
            ):
                status = connect_sketchfab_token("Bearer access-token")

            token_path = workbench_tool_module._sketchfab_token_path()
            stored = workbench_tool_module._read_optional_json(token_path)
            self.assertTrue(token_path.exists())
            self.assertEqual(token_path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(stored["access_token"], "access-token")
            self.assertTrue(status["connected"])
            self.assertEqual(status["token_source"], "cache")
            self.assertEqual(status["display_name"], "Artist One")

            disconnected = disconnect_sketchfab_auth()
            self.assertFalse(disconnected["connected"])
            self.assertEqual(disconnected["token_source"], "none")
            self.assertFalse(token_path.exists())

    def test_connect_sketchfab_token_rejects_invalid_token(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.dict(
            os.environ,
            {
                "XDG_CACHE_HOME": temp_dir,
                "CE_SKETCHFAB_API_TOKEN": "",
            },
            clear=False,
        ), mock.patch(
            "workbench_tool._sketchfab_profile_summary",
            side_effect=WorkbenchError("Sketchfab API request failed: HTTP 401"),
        ):
            with self.assertRaises(WorkbenchError):
                connect_sketchfab_token("invalid-token")

    def test_sketchfab_profile_request_uses_token_auth_scheme(self) -> None:
        response = mock.MagicMock()
        response.read.return_value = json.dumps(
            {
                "uid": "user-1",
                "username": "artist_one",
                "displayName": "Artist One",
                "profileUrl": "https://sketchfab.com/artist-one",
            }
        ).encode("utf-8")
        response.__enter__.return_value = response
        response.__exit__.return_value = False

        with mock.patch("urllib.request.urlopen", return_value=response) as urlopen_mock:
            profile = workbench_tool_module._sketchfab_profile_summary("access-token")

        request = urlopen_mock.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "Token access-token")
        self.assertEqual(profile["display_name"], "Artist One")

    def test_sketchfab_auth_status_prefers_env_token_over_cached_token(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.dict(
            os.environ,
            {
                "XDG_CACHE_HOME": temp_dir,
                "CE_SKETCHFAB_API_TOKEN": "env-token",
            },
            clear=False,
        ):
            workbench_tool_module._write_private_json(
                workbench_tool_module._sketchfab_token_path(),
                {
                    "access_token": "cache-token",
                    "created_at": "2026-04-05T00:00:00Z",
                    "me": {"display_name": "Cached Artist"},
                },
            )
            with mock.patch(
                "workbench_tool._sketchfab_profile_summary",
                return_value={
                    "uid": "env-user",
                    "username": "env_artist",
                    "display_name": "Env Artist",
                    "profile_url": "https://sketchfab.com/env-artist",
                },
            ):
                status = sketchfab_auth_status()
                token = resolve_sketchfab_access_token()

        self.assertTrue(status["configured"])
        self.assertTrue(status["connected"])
        self.assertEqual(status["token_source"], "env")
        self.assertEqual(status["display_name"], "Env Artist")
        self.assertEqual(token, "env-token")

    def test_disconnect_sketchfab_env_managed_token_keeps_connection(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "CE_SKETCHFAB_API_TOKEN": "env-token",
            },
            clear=False,
        ), mock.patch(
            "workbench_tool._sketchfab_profile_summary",
            return_value={
                "uid": "env-user",
                "username": "env_artist",
                "display_name": "Env Artist",
                "profile_url": "https://sketchfab.com/env-artist",
            },
        ):
            status = disconnect_sketchfab_auth()

        self.assertTrue(status["connected"])
        self.assertEqual(status["token_source"], "env")
        self.assertIn("restart the server", status["message"].lower())

    def test_smithsonian_fetch_reports_search_only_runtime_error(self) -> None:
        candidate = {
            "provider": "smithsonian_open_access",
            "remote_id": "museum_shuttle",
            "remote_url": "https://3d.si.edu/object/3d/museum_shuttle",
            "title": "Museum Shuttle",
            "license_class": "candidate",
        }
        with mock.patch("workbench_model_source._fetch_text", return_value="CC0 Open Access"):
            with self.assertRaises(ModelSourceError) as raised:
                fetch_model_candidate(candidate, global_cache_root=Path(tempfile.gettempdir()))

        self.assertIn("search-only", str(raised.exception).lower())

    def test_poly_pizza_fetch_uses_cache_after_first_download(self) -> None:
        detail_html = """
        <meta name="twitter:player" content="https://modelviewer.dev/examples/twitter/player.html?src=https://static.poly.pizza/test-resource.glb&amp;poster=https://static.poly.pizza/test-resource.jpg">
        <script>window.__BOOTSTRAP__ = {"initialData":{"model":{"Title":"Test Ship","Licence":"CC0 1.0","ResourceID":"test-resource"}}};var a=1;</script>
        """
        candidate = {
            "provider": "poly_pizza",
            "remote_id": "test_ship",
            "remote_url": "https://poly.pizza/m/test_ship",
            "title": "Test Ship",
            "license_class": "cc0",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_root = Path(temp_dir)
            with mock.patch("workbench_model_source._fetch_text", return_value=detail_html), mock.patch(
                "workbench_model_source._fetch_url", return_value=b"glb-bytes"
            ) as fetch_bytes:
                first = fetch_poly_pizza(candidate, cache_root)
                second = fetch_poly_pizza(candidate, cache_root)

            self.assertEqual(first["raw_asset_path"], second["raw_asset_path"])
            self.assertEqual(fetch_bytes.call_count, 1)

    def test_nasa_fetch_rejects_logo_assets(self) -> None:
        candidate = {
            "provider": "nasa_3d",
            "remote_id": "logo_patch",
            "remote_url": "https://science.nasa.gov/3d-resources/logo-patch/",
            "title": "Mission Patch Logo",
            "license_class": "nasa_media_guidelines",
        }
        with mock.patch("workbench_model_source._fetch_text", return_value='<model-viewer src="https://assets.science.nasa.gov/model.glb"></model-viewer>'):
            with self.assertRaises(ModelSourceError):
                fetch_nasa(candidate, Path(tempfile.gettempdir()))

    def test_normalize_model_source_rejects_unsupported_formats(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_path = root / "mesh.stl"
            raw_path.write_text("solid mesh\nendsolid mesh\n", encoding="utf-8")

            with self.assertRaises(ModelSourceError):
                normalize_fetched_model_candidate(
                    {
                        "provider": "nasa_3d",
                        "remote_id": "mesh",
                        "remote_url": "https://science.nasa.gov/3d-resources/mesh/",
                        "raw_asset_path": str(raw_path),
                        "source_format": "stl",
                    },
                    project_root=root / "project-models",
                    seed=4242,
                )

    def test_normalize_model_source_reuses_existing_project_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path = root / "incoming.glb"
            source_path.write_bytes(b"glb-bytes")
            project_root = root / "project-models"
            selection_root = project_root / "model_source" / "sketchfab__head-model"
            selection_root.mkdir(parents=True, exist_ok=True)
            raw_copy_path = selection_root / "raw.glb"
            raw_copy_path.write_bytes(source_path.read_bytes())
            normalized_asset_path = selection_root / "normalized.obj"
            normalized_asset_path.write_text("o cached\n", encoding="utf-8")
            point_cache_payload = {
                "schema_version": 1,
                "provider": "sketchfab",
                "remote_id": "head-model",
                "remote_url": "https://sketchfab.com/3d-models/head-model",
                "source_format": "glb",
                "normalized_asset_path": str(normalized_asset_path),
                "point_count": 1,
                "bounds": {
                    "min_x": -1.0,
                    "max_x": 1.0,
                    "min_y": -1.0,
                    "max_y": 1.0,
                    "min_z": -1.0,
                    "max_z": 1.0,
                },
                "subject_frame": {"space": "model", "forward_axis": [0.0, 0.0, 1.0]},
                "points": [[0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.5]],
            }
            point_cache_path = selection_root / "points.json"
            point_cache_path.write_text(json.dumps(point_cache_payload, indent=2) + "\n", encoding="utf-8")

            with mock.patch("workbench_model_source._load_mesh", side_effect=AssertionError("cache should be reused")):
                normalized = normalize_fetched_model_candidate(
                    {
                        "provider": "sketchfab",
                        "provider_label": "Sketchfab",
                        "remote_id": "head-model",
                        "remote_url": "https://sketchfab.com/3d-models/head-model",
                        "raw_asset_path": str(source_path),
                        "source_format": "glb",
                    },
                    project_root=project_root,
                    seed=4242,
                )

            self.assertEqual(normalized["status"], MODEL_SOURCE_STATUS_SELECTED)
            self.assertEqual(normalized["raw_asset_path"], str(raw_copy_path))
            self.assertEqual(normalized["normalized_asset_path"], str(normalized_asset_path))
            self.assertEqual(normalized["point_cache_path"], str(point_cache_path))
            self.assertEqual(normalized["subject_frame"]["space"], "model")
            self.assertTrue(normalized["point_cache_sha256"])

    def test_export_shot_requires_approved_mask(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_image = self._write_scenic_source_image(root)
            args = self._init_args(root, source_image)

            with mock.patch("workbench_tool.generate_auto_proposal_mask", return_value=(self._proposal_mask((960, 540)), "vision_saliency")):
                init_project_bundle(args)

            export_args = Namespace(
                project=args.project,
                output=str(root / "exports" / "proof.mp4"),
                manifest_output=None,
                poster_output=None,
                still_output=None,
                snapshot_id="snapshot_initial",
                width=None,
                height=None,
                frames=None,
                fps=None,
                min_duration_seconds=None,
                command="export-shot",
                repo_root=str(ROOT),
            )

            with self.assertRaises(WorkbenchError):
                export_project_shot(export_args)

    def test_export_request_respects_min_duration_over_requested_frames(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_image = self._write_isolated_source_image(root)
            init_args = self._init_args(root, source_image)
            init_project_bundle(init_args)
            project = load_project(Path(init_args.project))

            export_args = Namespace(
                project=init_args.project,
                output=None,
                manifest_output=None,
                poster_output=None,
                still_output=None,
                snapshot_id=None,
                width=None,
                height=None,
                frames=33,
                fps=24,
                min_duration_seconds=None,
            )
            request = build_export_request(project, export_args)

            self.assertEqual(request.frames, 120)
            self.assertEqual(request.fps, 24)
            self.assertEqual(request.duration_seconds, 5.0)

    def test_export_request_defaults_alpha_exports_to_mov(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_image = self._write_isolated_source_image(root)
            init_args = self._init_args(root, source_image)
            init_project_bundle(init_args)
            project = load_project(Path(init_args.project))

            export_args = Namespace(
                project=init_args.project,
                output=None,
                manifest_output=None,
                poster_output=None,
                still_output=None,
                snapshot_id=None,
                width=None,
                height=None,
                frames=24,
                fps=24,
                min_duration_seconds=1.0,
                alpha=True,
            )
            request = build_export_request(project, export_args)

            self.assertTrue(request.alpha)
            self.assertEqual(request.output_path.suffix, ".mov")
            self.assertIsNone(request.master_output_path)

    def test_export_request_defaults_opaque_exports_create_mp4_primary_and_master_mkv(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_image = self._write_isolated_source_image(root)
            init_args = self._init_args(root, source_image)
            init_project_bundle(init_args)
            project = load_project(Path(init_args.project))

            export_args = Namespace(
                project=init_args.project,
                output=None,
                manifest_output=None,
                poster_output=None,
                still_output=None,
                snapshot_id=None,
                width=None,
                height=None,
                frames=24,
                fps=24,
                min_duration_seconds=1.0,
                alpha=False,
            )
            request = build_export_request(project, export_args)

            self.assertFalse(request.alpha)
            self.assertEqual(request.output_path.suffix, ".mp4")
            self.assertIsNotNone(request.master_output_path)
            self.assertEqual(request.master_output_path.suffix, ".mkv")
            self.assertTrue(request.master_output_path.name.endswith(".master.mkv"))

    def test_export_request_rejects_non_alpha_mkv_output_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_image = self._write_isolated_source_image(root)
            init_args = self._init_args(root, source_image)
            init_project_bundle(init_args)
            project = load_project(Path(init_args.project))

            export_args = Namespace(
                project=init_args.project,
                output=str(root / "exports" / "proof.master.mkv"),
                manifest_output=None,
                poster_output=None,
                still_output=None,
                snapshot_id=None,
                width=None,
                height=None,
                frames=24,
                fps=24,
                min_duration_seconds=1.0,
                alpha=False,
            )

            with self.assertRaises(WorkbenchError):
                build_export_request(project, export_args)

    def test_encode_frames_to_video_uses_high_fidelity_safari_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            frames_dir = Path(temp_dir)
            output_path = frames_dir / "preview.mp4"
            with mock.patch("workbench_tool.shutil.which", return_value="/usr/bin/ffmpeg"), mock.patch(
                "workbench_tool.run_checked_command",
            ) as run_checked:
                workbench_tool_module.encode_frames_to_video(frames_dir, 24, output_path, alpha=False)

            command = run_checked.call_args.args[0]
            self.assertEqual(command[command.index("-c:v") + 1], "libx264")
            self.assertEqual(command[command.index("-preset") + 1], "veryslow")
            self.assertEqual(command[command.index("-profile:v") + 1], "high")
            self.assertEqual(command[command.index("-crf") + 1], "10")
            self.assertEqual(command[command.index("-pix_fmt") + 1], "yuv420p")
            self.assertEqual(command[command.index("-movflags") + 1], "+faststart")
            self.assertEqual(command[-1], str(output_path))

    def test_encode_frames_to_lossless_master_video_uses_ffv1_mkv(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            frames_dir = Path(temp_dir)
            output_path = frames_dir / "preview.master.mkv"
            with mock.patch("workbench_tool.shutil.which", return_value="/usr/bin/ffmpeg"), mock.patch(
                "workbench_tool.run_checked_command",
            ) as run_checked:
                workbench_tool_module.encode_frames_to_lossless_master_video(frames_dir, 24, output_path)

            command = run_checked.call_args.args[0]
            self.assertEqual(command[command.index("-c:v") + 1], "ffv1")
            self.assertEqual(command[command.index("-pix_fmt") + 1], "bgra")
            self.assertEqual(command[-1], str(output_path))

    def test_render_frame_can_keep_background_transparent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_image = self._write_isolated_source_image(root)
            init_args = self._init_args(root, source_image)
            init_project_bundle(init_args)
            project_path = Path(init_args.project)
            project = load_project(project_path)
            particles = generate_active_particle_specs(project_path, project)

            frame = render_frame(
                project=project,
                source_image=Image.new("RGBA", (4, 4), (0, 0, 0, 0)),
                mask_image=Image.new("L", (4, 4), 255),
                particles=particles,
                width=320,
                height=192,
                frame_index=0,
                total_frames=24,
                transparent_background=True,
            )

            self.assertEqual(frame.getpixel((0, 0))[3], 0)

    def test_export_project_shot_alpha_manifest_and_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_image = self._write_isolated_source_image(root)
            init_args = self._init_args(root, source_image)
            init_project_bundle(init_args)

            def fake_encode(_frames_dir: Path, _fps: int, output_path: Path, *, alpha: bool = False) -> None:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text("video", encoding="utf-8")
                self.assertTrue(alpha)
                self.assertEqual(output_path.suffix, ".mov")

            export_args = Namespace(
                project=init_args.project,
                output=None,
                manifest_output=None,
                poster_output=None,
                still_output=None,
                snapshot_id="snapshot_initial",
                width=None,
                height=None,
                frames=24,
                fps=24,
                min_duration_seconds=1.0,
                alpha=True,
                command="export-shot",
                repo_root=str(ROOT),
            )

            with mock.patch("workbench_tool.serve_export_session", new=self._fake_export_session()), mock.patch(
                "workbench_tool.export_frames_with_webgl",
                side_effect=self._fake_webgl_export(),
            ), mock.patch("workbench_tool.encode_frames_to_video", side_effect=fake_encode):
                manifest = export_project_shot(export_args)

            self.assertTrue(manifest["alpha"])
            self.assertEqual(Path(manifest["output_path"]).suffix, ".mov")
            self.assertEqual(manifest["master_output_path"], "")
            self.assertFalse(manifest["master_lossless"])

    def test_ui_shell_uses_workflow_rail_upload_surface_and_webgl_viewer(self) -> None:
        html = (ROOT / "scripts" / "workbench_static" / "index.html").read_text(encoding="utf-8")
        javascript = (ROOT / "scripts" / "workbench_static" / "workbench.js").read_text(encoding="utf-8")
        capture_script = (ROOT / "scripts" / "workbench_chrome_capture.mjs").read_text(encoding="utf-8")

        self.assertIn("workflow-strip", html)
        self.assertIn("Find A Subject Model", html)
        self.assertIn("model-source-query", html)
        self.assertIn("model-source-thumbnail", html)
        self.assertIn("model-source-thumbnail-fallback", html)
        self.assertIn("Upload Local Model", html)
        self.assertIn("Browse External Libraries", html)
        self.assertIn("Paste Sketchfab personal token", html)
        self.assertIn('id="sketchfab-token-input"', html)
        self.assertIn('id="model-resource-modal-trigger"', html)
        self.assertIn('id="model-resource-modal"', html)
        self.assertIn('id="model-resource-modal-close"', html)
        self.assertIn('id="model-source-resources"', html)
        self.assertIn('aria-controls="model-resource-modal"', html)
        self.assertIn(".modal-shell[hidden]", html)
        self.assertIn("Burn Video", html)
        self.assertIn("Search for an object or subject first", html)
        self.assertIn("effect-viewer", html)
        self.assertIn("Particle View", html)
        self.assertIn("Raw Model", html)
        self.assertIn('id="viewport-tab-particle"', html)
        self.assertIn('id="viewport-tab-model"', html)
        self.assertIn('id="preview-warning"', html)
        self.assertIn('/assets/workbench.js', html)
        self.assertIn("media-preview-shell", html)
        self.assertIn('id="burn-preview-shell"', html)
        self.assertIn('id="burn-master-path"', html)
        self.assertIn("Safari Preview MP4", html)
        self.assertIn("Exact Master (FFV1 MKV)", html)
        self.assertIn("Poster PNG (middle frame)", html)
        self.assertIn("Still PNG (final frame)", html)
        self.assertIn("The main preview shows the Safari-playable MP4.", html)
        self.assertIn("Save Preset…", html)
        self.assertIn('data-section-key="model"', html)
        self.assertIn('id="model-controls"', html)
        self.assertIn('id="effect-autosave-status"', html)
        self.assertIn("section-title-row", html)
        self.assertIn('id="model-selection-author"', html)
        self.assertIn('id="model-selection-attribution"', html)
        self.assertIn('input[type="number"]', html)
        self.assertIn('input[type="password"]', html)
        self.assertIn("-webkit-text-fill-color: var(--text);", html)
        self.assertIn(".control-number:focus", html)
        self.assertIn(".control-number:disabled", html)
        self.assertIn("Move to the Effect step to author particle behavior.", javascript)
        self.assertIn('"/api/model-source/sketchfab/auth/status"', javascript)
        self.assertIn('"/api/model-source/sketchfab/token/connect"', javascript)
        self.assertIn("Paste a Sketchfab personal token", javascript)
        self.assertIn("modelSourceThumbnailMarkup", javascript)
        self.assertIn("wireModelSourceThumbnails", javascript)
        self.assertIn("No preview", javascript)
        self.assertIn("openModelResourceModal", javascript)
        self.assertIn("closeModelResourceModal", javascript)
        self.assertIn("syncModelResourceModalState(false);", javascript)
        self.assertIn("wireModelResourceModal", javascript)
        self.assertIn("syncMediaViewportRatio", javascript)
        self.assertIn("currentViewportTab", javascript)
        self.assertIn("setViewportTab", javascript)
        self.assertIn("raw_model_mesh", javascript)
        self.assertIn("raw_model_points", javascript)
        self.assertIn("raw_model_fit_camera", javascript)
        self.assertIn("this.rawModelMeshGroup", javascript)
        self.assertIn("this.rawModelCameraState", javascript)
        self.assertIn("Rotate Y", javascript)
        self.assertIn("continuous: true", javascript)
        self.assertIn('"/vendor/TrackballControls.js"', javascript)
        self.assertNotIn('"/vendor/OrbitControls.js"', javascript)
        self.assertIn("this.controls.rotateSpeed = 2.4;", javascript)
        self.assertIn("reset_camera", javascript)
        self.assertIn("raw_model_reset_camera", javascript)
        self.assertIn("signedAngleAroundAxis", javascript)
        self.assertIn("cameraState?.roll", javascript)
        self.assertIn('payload.model_source = {', javascript)
        self.assertIn("displayScale: 100", javascript)
        self.assertIn("displayScale: 10", javascript)
        self.assertIn("No emission: raise Breakup to release particles.", javascript)
        self.assertIn("manifestSnapshotId !== approvalSnapshotId", javascript)
        self.assertIn("lastBurnManifest = null;", javascript)
        self.assertIn('master_output_path: lastBurnManifest.master_output_path || approval.master_output_path || ""', javascript)
        self.assertIn('document.getElementById("burn-master-path")', javascript)
        self.assertIn("exportEffectFrame", javascript)
        self.assertIn('postJson("/api/preset/save"', javascript)
        self.assertIn('postJson("/api/preset/apply"', javascript)
        self.assertIn('postJson("/api/snapshot/select"', javascript)
        self.assertIn("renderControlSectionHeaders", javascript)
        self.assertIn("control-number", javascript)
        self.assertIn("tooltip-trigger", javascript)
        self.assertIn("snapshot-badge", javascript)
        self.assertIn("All changes autosave.", javascript)
        self.assertIn("const drawBufferHeight = Math.max(1, height * pixelRatio);", javascript)
        self.assertIn("this.trailMaterial.uniforms.focalPx.value = focalPx;", javascript)
        self.assertIn("pixelRatio: options.pixelRatio ?? 1", javascript)
        self.assertIn("--force-device-scale-factor=1", capture_script)
        self.assertNotIn("Save Scene", html)
        self.assertNotIn("mask-canvas", html)
        self.assertNotIn("Upload Candidate", html)
        self.assertNotIn("Approve Mask", html)
        self.assertNotIn('id="burn-poster"', html)
        self.assertNotIn('id="preview-image"', html)


if __name__ == "__main__":
    unittest.main()
