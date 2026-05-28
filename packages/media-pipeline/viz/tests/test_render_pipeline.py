from __future__ import annotations

import json
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

try:
    from PIL import Image
except ModuleNotFoundError:  # pragma: no cover - dependency varies by environment
    Image = None


ROOT = Path("/Users/mike/CascadeEffects/packages/media-pipeline/viz")
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from render_tool import (  # noqa: E402
    HeadlessComfyRunner,
    command_pipeline,
    package_grid_ranking_policy,
    package_grid_softpass_policy,
    resolve_quality_profile_settings,
)
from workflow_tool import WorkflowError, write_json  # noqa: E402


BASE_SEED = 972054013131368


def install_flux2_model_stubs(models_dir: Path) -> None:
    for directory_name, model_name in (
        ("diffusion_models", "flux2-dev.safetensors"),
        ("vae", "flux2-vae.safetensors"),
        ("text_encoders", "mistral_3_small_flux2_bf16.safetensors"),
        ("text_encoders", "clip_l.safetensors"),
    ):
        target_dir = models_dir / directory_name
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / model_name).write_text("stub\n", encoding="utf-8")


class FakeRunner:
    def __init__(
        self,
        root: Path,
        *,
        fail_all_candidates: bool = False,
        with_hero_model: bool = True,
    ) -> None:
        self.root = root
        self.runs_root = root / "runs"
        self.comfy_output_dir = root / "output"
        self.models_root = root / "models"
        self.server_url = "http://fake-comfy:8188"
        self.fail_all_candidates = fail_all_candidates
        self.render_calls: list[tuple[str, int]] = []
        self.visual_qc_calls: list[tuple[str, int]] = []
        self.runs_root.mkdir(parents=True, exist_ok=True)
        self.comfy_output_dir.mkdir(parents=True, exist_ok=True)
        if with_hero_model:
            install_flux2_model_stubs(self.models_root)

    def build_stage_result(self, family: str, preset: str, stage: str, overrides: dict[str, object]) -> SimpleNamespace:
        seed = int(overrides.get("selected_seed", BASE_SEED))
        params = {
            "seed": seed,
            "selected_seed": seed,
            "variant_count": 1,
            "seed_mode": "search",
            "width": 1344,
            "height": 768,
        }
        manifest = {
            "pipeline_strategy": {
                "seed_policy": "search",
                "draft_candidate_count": 6,
                "hero_model": "flux2-dev",
                "hero_refine_denoise": 0.22,
                "semantic_qc_profile": (
                    "opening_culture_cluster" if preset == "opening_culture_cluster" else "challenger_mission_control"
                ),
            }
        }
        return SimpleNamespace(params=params, manifest=manifest)

    def repair_policy_should_run(self, family: str, preset: str, mode: str) -> tuple[bool, None]:
        return False, None

    def typography_should_run(self, family: str, preset: str, mode: str) -> tuple[bool, None]:
        return False, None

    def render_stage_once(
        self,
        family: str,
        preset: str,
        stage: str,
        overrides: dict[str, object],
        invocation: str,
        pipeline_id: str | None = None,
    ) -> dict[str, object]:
        seed = int(overrides.get("selected_seed", BASE_SEED))
        artifact_path = self.comfy_output_dir / f"{stage}_{seed}.png"
        artifact_path.write_text(f"{stage}:{seed}\n", encoding="utf-8")
        run_manifest_path = self.runs_root / family / preset / f"{stage}_{seed}.run.json"
        write_json(
            run_manifest_path,
            {
                "stage": stage,
                "seed": seed,
                "invocation": invocation,
                "pipeline_id": pipeline_id,
            },
        )
        self.render_calls.append((stage, seed))
        return {
            "output_files": [artifact_path],
            "run_manifest_path": run_manifest_path,
        }

    def relative_output_path(self, path: Path) -> str:
        return str(path.relative_to(self.comfy_output_dir))

    def run_visual_qc_audit(
        self,
        artifact_path: Path,
        *,
        family: str,
        preset: str,
        semantic_profile: str = "",
        semantic_stage: str = "final",
        ban_scanlines: bool | None = None,
        contract_config: dict[str, object] | None = None,
        debug_dir: Path | None = None,
        allow_invalid_json: bool = False,
    ) -> dict[str, object]:
        del allow_invalid_json
        seed = int(artifact_path.stem.rsplit("_", 1)[-1])
        self.visual_qc_calls.append((semantic_stage, seed))
        if semantic_stage == "candidate":
            ranking_score = {
                BASE_SEED: 6.2,
                BASE_SEED + 1: 8.9,
                BASE_SEED + 2: 5.1,
                BASE_SEED + 3: 6.8,
                BASE_SEED + 4: 6.4,
                BASE_SEED + 5: 5.0,
            }.get(seed, 4.0)
            failures = ["semantic hard fail: too_abstract"] if self.fail_all_candidates or ranking_score < 6.5 else []
            return {
                "status": "failed" if failures else "ok",
                "score": 0.0,
                "threshold": 2.0,
                "metrics": {},
                "warnings": [],
                "failures": failures,
                "semantic": {
                    "ranking_score": ranking_score,
                },
            }
        return {
            "status": "ok",
            "score": 0.0,
            "threshold": 2.0,
            "metrics": {},
            "warnings": [],
            "failures": [],
            "semantic": {
                "ranking_score": 8.7,
            },
        }

    def write_visual_qc_run_manifest(
        self,
        *,
        family: str,
        preset: str,
        source_stage: str,
        validation_stage: str,
        artifact_path: Path,
        audit_summary: dict[str, object],
        invocation: str,
        pipeline_id: str | None,
        candidate_seed: int,
    ) -> Path:
        path = self.runs_root / family / preset / f"{validation_stage}_{candidate_seed}.run.json"
        write_json(
            path,
            {
                "source_stage": source_stage,
                "validation_stage": validation_stage,
                "artifact_path": str(artifact_path),
                "audit_summary": audit_summary,
                "invocation": invocation,
                "pipeline_id": pipeline_id,
            },
        )
        return path

    def run_zero_letter_audit(self, artifact_path: Path, *, debug_dir: Path | None = None) -> dict[str, object]:
        return {
            "status": "ok",
            "unapproved_text": [],
            "warnings": [],
            "failures": [],
        }

    def write_zero_letter_audit_run_manifest(
        self,
        *,
        family: str,
        preset: str,
        stage: str,
        artifact_path: Path,
        audit_summary: dict[str, object],
        invocation: str,
        pipeline_id: str | None,
        selected_seed: int,
    ) -> Path:
        path = self.runs_root / family / preset / f"{stage}_zero_letter_{selected_seed}.run.json"
        write_json(
            path,
            {
                "stage": stage,
                "artifact_path": str(artifact_path),
                "audit_summary": audit_summary,
                "invocation": invocation,
                "pipeline_id": pipeline_id,
            },
        )
        return path


class RenderPipelineTests(unittest.TestCase):
    def make_args(self) -> Namespace:
        return Namespace(
            family="scene_still",
            preset="challenger_mission_control",
            selected_seed=None,
            overrides=[],
            typography="off",
            source_text_repair="off",
            quality_profile="standard",
            delivery_mode="strict",
        )

    def make_opening_args(self) -> Namespace:
        opening_payload = {
            "subject_descriptor": "space shuttle stack on pad prepared for isolation and liftoff",
            "required_reads": [
                "VHS cassette",
                "Cassette boombox radio",
                "White high-top sneaker",
                "Aluminum soda can",
                "Cube puzzle",
                "Beige home computer CRT",
                "Space Shuttle Challenger",
            ],
            "slots": [
                {
                    "slot_id": "vhs_cassette",
                    "display_label": "VHS cassette",
                    "role": "supporting_object",
                    "asset_path": "/tmp/vhs.png",
                },
                {
                    "slot_id": "boombox_radio",
                    "display_label": "Cassette boombox radio",
                    "role": "supporting_object",
                    "asset_path": "/tmp/boombox.png",
                },
                {
                    "slot_id": "high_top_sneaker",
                    "display_label": "White high-top sneaker",
                    "role": "supporting_object",
                    "asset_path": "/tmp/sneaker.png",
                },
                {
                    "slot_id": "aluminum_soda_can",
                    "display_label": "Aluminum soda can",
                    "role": "supporting_object",
                    "asset_path": "/tmp/can.png",
                },
                {
                    "slot_id": "cube_puzzle",
                    "display_label": "Cube puzzle",
                    "role": "supporting_object",
                    "asset_path": "/tmp/cube.png",
                },
                {
                    "slot_id": "beige_home_computer_crt",
                    "display_label": "Beige home computer CRT",
                    "role": "supporting_object",
                    "asset_path": "/tmp/crt.png",
                },
                {
                    "slot_id": "space_shuttle_challenger",
                    "display_label": "Space Shuttle Challenger",
                    "role": "subject_object",
                    "asset_path": "/tmp/challenger.png",
                },
            ],
        }
        return Namespace(
            family="scene_still",
            preset="opening_culture_cluster",
            selected_seed=BASE_SEED + 1,
            overrides=[f"opening_payload={json.dumps(opening_payload)}"],
            typography="off",
            source_text_repair="off",
            quality_profile="standard",
            delivery_mode="strict",
        )

    def latest_pipeline_manifest(self, root: Path, preset: str = "challenger_mission_control") -> dict[str, object]:
        manifests = sorted((root / "runs" / "scene_still" / preset).glob("*__pipeline.run.json"))
        self.assertTrue(manifests)
        return json.loads(manifests[-1].read_text(encoding="utf-8"))

    def test_subject_reference_stage_reuses_existing_staged_asset(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-render-runner-") as temp_root:
            root = Path(temp_root)
            repo_root = root / "repo"
            repo_root.mkdir(parents=True, exist_ok=True)
            source_path = repo_root / "references" / "hero.png"
            source_path.parent.mkdir(parents=True, exist_ok=True)
            source_path.write_text("hero", encoding="utf-8")
            models_root = root / "models"
            (models_root / "clip_vision").mkdir(parents=True, exist_ok=True)
            (models_root / "clip_vision" / "clip_vision_g.safetensors").write_text("stub", encoding="utf-8")
            comfy_root = root / "comfy"
            args = Namespace(
                repo_root=str(repo_root),
                models_root=str(models_root),
                comfy_workflows_dir=str(root / "workflows"),
                comfy_output_dir=str(comfy_root / "output"),
                references_root=str(repo_root / "references"),
                comfy_input_dir=str(comfy_root / "input"),
                comfy_temp_dir=str(comfy_root / "temp"),
                comfy_user_dir=str(comfy_root / "user"),
                comfy_extra_models_config=str(root / "extra_models_config.yaml"),
                comfy_python=str(root / "python"),
                comfy_main_py=str(root / "main.py"),
                comfy_clip_vision_model="clip_vision_g.safetensors",
                host="127.0.0.1",
                port=8188,
                pid_file=str(root / "runner.pid"),
                log_file=str(root / "runner.log"),
            )
            Path(args.comfy_python).write_text("stub", encoding="utf-8")
            Path(args.comfy_main_py).write_text("stub", encoding="utf-8")
            Path(args.comfy_extra_models_config).write_text("stub", encoding="utf-8")
            frontend_root = Path(args.comfy_main_py).parent / "web_custom_versions" / "desktop_app"
            frontend_root.mkdir(parents=True, exist_ok=True)
            runner = HeadlessComfyRunner(args)
            staged_path, copied_first = runner.stage_subject_reference_asset(
                source_path,
                family="shorts_scene_plate",
                preset="challenger_warning_cold",
            )
            staged_path_second, copied_second = runner.stage_subject_reference_asset(
                source_path,
                family="shorts_scene_plate",
                preset="challenger_warning_cold",
            )
            self.assertTrue(copied_first)
            self.assertFalse(copied_second)
            self.assertEqual(staged_path, staged_path_second)
            self.assertTrue(
                str(staged_path).startswith(str(Path(args.comfy_input_dir).resolve()))
            )

    def test_prepare_subject_reference_overrides_rejects_stale_generated_plate(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-render-stale-") as temp_root:
            root = Path(temp_root)
            models_root = root / "models"
            (models_root / "clip_vision").mkdir(parents=True, exist_ok=True)
            (models_root / "clip_vision" / "clip_vision_g.safetensors").write_text("stub", encoding="utf-8")
            args = Namespace(
                repo_root=str(ROOT),
                models_root=str(models_root),
                comfy_workflows_dir=str(root / "workflows"),
                comfy_output_dir=str(root / "output"),
                references_root=str(ROOT / "references"),
                comfy_input_dir=str(root / "input"),
                comfy_temp_dir=str(root / "temp"),
                comfy_user_dir=str(root / "user"),
                comfy_extra_models_config=str(root / "extra_models_config.yaml"),
                comfy_python=str(root / "python"),
                comfy_main_py=str(root / "main.py"),
                comfy_clip_vision_model="clip_vision_g.safetensors",
                host="127.0.0.1",
                port=8188,
                pid_file=str(root / "runner.pid"),
                log_file=str(root / "runner.log"),
            )
            Path(args.comfy_python).write_text("stub", encoding="utf-8")
            Path(args.comfy_main_py).write_text("stub", encoding="utf-8")
            Path(args.comfy_extra_models_config).write_text("stub", encoding="utf-8")
            frontend_root = Path(args.comfy_main_py).parent / "web_custom_versions" / "desktop_app"
            frontend_root.mkdir(parents=True, exist_ok=True)
            stale_plate = (
                root
                / "references"
                / "episodes"
                / "challenger"
                / "subject_reference_plates"
                / "generated"
                / "challenger_thesis_close.png"
            )
            stale_plate.parent.mkdir(parents=True, exist_ok=True)
            stale_plate.write_text("png", encoding="utf-8")

            runner = HeadlessComfyRunner(args)
            with self.assertRaises(WorkflowError) as exc:
                runner.prepare_subject_reference_overrides(
                    "shorts_scene_plate",
                    "challenger_thesis_close",
                    "draft_txt2img",
                    {"subject_reference_image": str(stale_plate)},
                )
            self.assertIn("subject_reference_image is stale", str(exc.exception))

    def test_prepare_subject_reference_overrides_stages_midjourney_grid_for_runtime(self) -> None:
        if Image is None:
            self.skipTest("Pillow is not available in this environment.")
        with tempfile.TemporaryDirectory(prefix="ce-render-grid-stage-") as temp_root:
            root = Path(temp_root)
            models_root = root / "models"
            (models_root / "clip_vision").mkdir(parents=True, exist_ok=True)
            (models_root / "clip_vision" / "clip_vision_g.safetensors").write_text("stub", encoding="utf-8")
            args = Namespace(
                repo_root=str(ROOT),
                models_root=str(models_root),
                comfy_workflows_dir=str(root / "workflows"),
                comfy_output_dir=str(root / "output"),
                references_root=str(ROOT / "references"),
                comfy_input_dir=str(root / "input"),
                comfy_temp_dir=str(root / "temp"),
                comfy_user_dir=str(root / "user"),
                comfy_extra_models_config=str(root / "extra_models_config.yaml"),
                comfy_python=str(root / "python"),
                comfy_main_py=str(root / "main.py"),
                comfy_clip_vision_model="clip_vision_g.safetensors",
                host="127.0.0.1",
                port=8188,
                pid_file=str(root / "runner.pid"),
                log_file=str(root / "runner.log"),
            )
            Path(args.comfy_python).write_text("stub", encoding="utf-8")
            Path(args.comfy_main_py).write_text("stub", encoding="utf-8")
            Path(args.comfy_extra_models_config).write_text("stub", encoding="utf-8")
            frontend_root = Path(args.comfy_main_py).parent / "web_custom_versions" / "desktop_app"
            frontend_root.mkdir(parents=True, exist_ok=True)

            runner = HeadlessComfyRunner(args)
            overrides, manifest = runner.prepare_subject_reference_overrides(
                "shorts_scene_plate",
                "challenger_warning_cold",
                "draft_txt2img",
                {},
            )
            assert manifest is not None
            subject_reference = manifest["subject_reference"]
            midjourney_package = manifest["midjourney_package"]
            self.assertTrue(midjourney_package["active"])
            self.assertEqual(midjourney_package["package_id"], "challenger_short_minimal_surreal_v1__midjourney_v1")
            self.assertEqual(midjourney_package["shot_id"], "beat_01")
            self.assertEqual(len(midjourney_package["reference_files"]), 3)
            self.assertTrue(midjourney_package["reference_grid_path"].endswith("beat_01__1024x1792.png"))
            self.assertTrue(midjourney_package["staged_reference_grid_path"].endswith("beat_01__reference_grid.png"))
            self.assertTrue(midjourney_package["adapter"]["active"])
            self.assertEqual(midjourney_package["adapter"]["grid_layout_template"], "detail_left_bias_triptych")
            self.assertEqual(midjourney_package["adapter"]["included_reference_indices"], [1, 0, 2])
            self.assertEqual(len(midjourney_package["grid_tiles"]), 3)
            self.assertTrue(subject_reference["staged_input_path"].endswith("beat_01__reference_grid.png"))
            self.assertEqual(subject_reference["runtime_source_path"], midjourney_package["reference_grid_path"])
            self.assertNotIn("subject_reference_runtime_mask", overrides)
            self.assertEqual(
                overrides["subject_reference_runtime_image"],
                "cascadeeffects/midjourney_package_grids/shorts_scene_plate/challenger_warning_cold/beat_01__reference_grid.png",
            )

    def test_package_grid_softpass_policy_reads_adapter_manifest(self) -> None:
        policy = package_grid_softpass_policy(
            {
                "midjourney_package": {
                    "active": True,
                    "adapter": {
                        "active": True,
                        "draft_visual_softpass": {
                            "enabled": True,
                            "allowed_visual_failures": [
                                "asymmetry_ratio_below_threshold",
                                "palette_discipline_below_threshold",
                            ],
                        },
                    },
                }
            }
        )
        assert policy is not None
        self.assertIn("asymmetry_ratio_below_threshold", policy["allowed_visual_failures"])
        self.assertIn("subtitle_band_intrusion", policy["hard_block_failures"])

    def test_package_grid_ranking_policy_reads_adapter_manifest(self) -> None:
        policy = package_grid_ranking_policy(
            {
                "midjourney_package": {
                    "active": True,
                    "adapter": {
                        "active": True,
                        "steer_target": "cold_pipe_winter_signal",
                        "steer_keep_traits": ["winter haze"],
                        "steer_avoid_traits": ["tower hero framing"],
                        "ranking_bias_tags": ["winter_haze", "cold_pipe_detail"],
                    },
                }
            }
        )
        assert policy is not None
        self.assertEqual(policy["steer_target"], "cold_pipe_winter_signal")
        self.assertEqual(policy["steer_keep_traits"], ["winter haze"])
        self.assertEqual(policy["ranking_bias_tags"], ("winter_haze", "cold_pipe_detail"))

    def test_pipeline_allows_adapter_softpass_candidate_into_refine(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-pipeline-softpass-") as temp_root:
            root = Path(temp_root)
            runner = FakeRunner(root)

            def custom_visual_qc(
                artifact_path: Path,
                *,
                family: str,
                preset: str,
                semantic_profile: str = "",
                semantic_stage: str = "final",
                ban_scanlines: bool | None = None,
                contract_config: dict[str, object] | None = None,
                debug_dir: Path | None = None,
                allow_invalid_json: bool = False,
            ) -> dict[str, object]:
                del allow_invalid_json
                seed = int(artifact_path.stem.rsplit("_", 1)[-1])
                runner.visual_qc_calls.append((semantic_stage, seed))
                if semantic_stage == "candidate":
                    if seed == BASE_SEED:
                        return {
                            "status": "failed",
                            "score": 0.0,
                            "threshold": 2.0,
                            "metrics": {},
                            "warnings": [],
                            "failures": [
                                "asymmetry_ratio_below_threshold",
                                "palette_discipline_below_threshold",
                            ],
                            "semantic": {
                                "status": "ok",
                                "ranking_score": 9.2,
                                "failures": [],
                            },
                        }
                    return {
                        "status": "failed",
                        "score": 0.0,
                        "threshold": 2.0,
                        "metrics": {},
                        "warnings": [],
                        "failures": ["semantic hard fail: unrecognizable_anchor"],
                        "semantic": {
                            "status": "failed",
                            "ranking_score": 3.0,
                            "failures": ["semantic hard fail: unrecognizable_anchor"],
                        },
                    }
                return {
                    "status": "ok",
                    "score": 0.0,
                    "threshold": 2.0,
                    "metrics": {},
                    "warnings": [],
                    "failures": [],
                    "semantic": {"ranking_score": 8.8},
                }

            runner.run_visual_qc_audit = custom_visual_qc  # type: ignore[method-assign]
            with mock.patch(
                "render_tool.package_grid_softpass_policy",
                return_value={
                    "allowed_visual_failures": {
                        "asymmetry_ratio_below_threshold",
                        "palette_discipline_below_threshold",
                        "focal_clarity_below_threshold",
                    },
                    "hard_block_failures": {
                        "center_weighted_primary_subject",
                        "subtitle_band_intrusion",
                        "symmetry_too_high",
                        "subject_count_exceeds_limit",
                        "duplicate_human_identity",
                        "multiple_shuttle_heroes",
                        "unrecognizable_anchor",
                        "scenic_exterior_drift",
                        "text_artifacts",
                    },
                },
            ):
                result = command_pipeline(runner, self.make_args())

            self.assertEqual(result, 0)
            manifest = self.latest_pipeline_manifest(root)
            self.assertEqual(manifest["selected_candidate"]["seed"], BASE_SEED)
            self.assertTrue(manifest["candidate_scores"][str(BASE_SEED)]["softpass_eligible"])
            self.assertEqual(len([call for call in runner.render_calls if call[0] == "refine_img2img"]), 1)

    def test_pipeline_ranking_bias_reorders_softpass_candidates(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-pipeline-ranking-bias-") as temp_root:
            root = Path(temp_root)
            runner = FakeRunner(root)

            def custom_visual_qc(
                artifact_path: Path,
                *,
                family: str,
                preset: str,
                semantic_profile: str = "",
                semantic_stage: str = "final",
                ban_scanlines: bool | None = None,
                contract_config: dict[str, object] | None = None,
                debug_dir: Path | None = None,
                allow_invalid_json: bool = False,
            ) -> dict[str, object]:
                del allow_invalid_json
                seed = int(artifact_path.stem.rsplit("_", 1)[-1])
                runner.visual_qc_calls.append((semantic_stage, seed))
                if semantic_stage == "candidate":
                    return {
                        "status": "failed",
                        "score": 0.0,
                        "threshold": 2.0,
                        "metrics": {},
                        "warnings": [],
                        "failures": ["palette_discipline_below_threshold"],
                        "semantic": {
                            "status": "ok",
                            "ranking_score": 8.0 if seed == BASE_SEED else 8.8,
                            "notes": "industrial context and winter haze",
                            "failures": [],
                        },
                    }
                return {
                    "status": "ok",
                    "score": 0.0,
                    "threshold": 2.0,
                    "metrics": {},
                    "warnings": [],
                    "failures": [],
                    "semantic": {"ranking_score": 8.8},
                }

            runner.run_visual_qc_audit = custom_visual_qc  # type: ignore[method-assign]
            with mock.patch(
                "render_tool.package_grid_softpass_policy",
                return_value={
                    "allowed_visual_failures": {"palette_discipline_below_threshold"},
                    "hard_block_failures": set(),
                },
            ), mock.patch(
                "render_tool.package_grid_ranking_policy",
                return_value={
                    "steer_target": "cold_pipe_winter_signal",
                    "steer_keep_traits": ["winter haze"],
                    "steer_avoid_traits": ["tower hero framing"],
                    "ranking_bias_tags": ("winter_haze",),
                },
            ), mock.patch(
                "render_tool.candidate_ranking_bias",
                side_effect=lambda candidate_qc_summary, *, ranking_policy, artifact_path: (
                    (1.25, {"winter_haze": 1.25})
                    if artifact_path.name.endswith(f"{BASE_SEED}.png")
                    else (0.0, {})
                ),
            ):
                result = command_pipeline(runner, self.make_args())

            self.assertEqual(result, 0)
            manifest = self.latest_pipeline_manifest(root)
            self.assertEqual(manifest["selected_candidate"]["seed"], BASE_SEED)
            self.assertEqual(manifest["candidate_scores"][str(BASE_SEED)]["selection_score"], 9.25)
            self.assertEqual(
                manifest["candidate_scores"][str(BASE_SEED)]["ranking_bias_breakdown"],
                {"winter_haze": 1.25},
            )

    def test_quality_profiles_use_migrated_midjourney_candidate_counts(self) -> None:
        pipeline_strategy = {
            "seed_policy": "search",
            "draft_candidate_count": 4,
            "hero_model": "flux2-dev",
            "hero_refine_denoise": 0.18,
            "semantic_qc_profile": "shorts_scene_default",
        }
        self.assertEqual(
            resolve_quality_profile_settings(
                family="shorts_scene_plate",
                pipeline_strategy=pipeline_strategy,
                quality_profile="fast",
            )[
                "draft_candidate_count"
            ],
            1,
        )
        self.assertEqual(
            resolve_quality_profile_settings(
                family="shorts_scene_plate",
                pipeline_strategy=pipeline_strategy,
                quality_profile="standard",
            )[
                "draft_candidate_count"
            ],
            4,
        )
        self.assertEqual(
            resolve_quality_profile_settings(
                family="shorts_scene_plate",
                pipeline_strategy=pipeline_strategy,
                quality_profile="hero",
            )[
                "draft_candidate_count"
            ],
            8,
        )

    def test_standard_pipeline_ranks_candidates_and_selects_winner(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-pipeline-") as temp_root:
            root = Path(temp_root)
            runner = FakeRunner(root)
            result = command_pipeline(runner, self.make_args())
            self.assertEqual(result, 0)

            manifest = self.latest_pipeline_manifest(root)
            self.assertEqual(manifest["quality_profile"], "standard")
            self.assertEqual(len(manifest["draft_candidates"]), 6)
            self.assertEqual(manifest["selected_candidate"]["seed"], BASE_SEED + 1)
            self.assertEqual(len([call for call in runner.render_calls if call[0] == "draft_txt2img"]), 6)
            self.assertEqual(len([call for call in runner.render_calls if call[0] == "refine_img2img"]), 1)
            self.assertEqual(len([call for call in runner.render_calls if call[0] == "final_upscale"]), 1)

    def test_pipeline_fails_when_all_candidates_fail_semantic_qc(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-pipeline-") as temp_root:
            root = Path(temp_root)
            runner = FakeRunner(root, fail_all_candidates=True)
            with self.assertRaises(WorkflowError):
                command_pipeline(runner, self.make_args())

            manifest = self.latest_pipeline_manifest(root)
            self.assertEqual(manifest["status"], "failed")
            self.assertIn("No draft candidate cleared semantic QC", manifest["failure"])

    def test_pipeline_advisory_mode_delivers_when_all_candidates_fail_semantic_qc(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-pipeline-") as temp_root:
            root = Path(temp_root)
            runner = FakeRunner(root, fail_all_candidates=True)
            args = self.make_args()
            args.delivery_mode = "advisory"

            result = command_pipeline(runner, args)

            self.assertEqual(result, 0)
            manifest = self.latest_pipeline_manifest(root)
            self.assertEqual(manifest["status"], "advisory_success")
            self.assertTrue(manifest["delivery_advisory_used"])
            self.assertEqual(manifest["selected_candidate"]["seed"], BASE_SEED + 1)
            self.assertIn("No draft candidate cleared semantic QC", " ".join(manifest["delivery_notes"]))

    def test_pipeline_advisory_mode_keeps_output_when_final_visual_qc_fails(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-pipeline-") as temp_root:
            root = Path(temp_root)
            runner = FakeRunner(root)
            original_visual_qc = runner.run_visual_qc_audit

            def custom_visual_qc(
                artifact_path: Path,
                *,
                family: str,
                preset: str,
                semantic_profile: str = "",
                semantic_stage: str = "final",
                ban_scanlines: bool | None = None,
                contract_config: dict[str, object] | None = None,
                debug_dir: Path | None = None,
                allow_invalid_json: bool = False,
            ) -> dict[str, object]:
                del ban_scanlines, contract_config, debug_dir, allow_invalid_json
                summary = original_visual_qc(
                    artifact_path,
                    family=family,
                    preset=preset,
                    semantic_profile=semantic_profile,
                    semantic_stage=semantic_stage,
                )
                if semantic_stage == "final":
                    summary = dict(summary)
                    summary["status"] = "failed"
                    summary["failures"] = ["subtitle_band_intrusion"]
                return summary

            runner.run_visual_qc_audit = custom_visual_qc  # type: ignore[method-assign]
            args = self.make_args()
            args.delivery_mode = "advisory"

            result = command_pipeline(runner, args)

            self.assertEqual(result, 0)
            manifest = self.latest_pipeline_manifest(root)
            self.assertEqual(manifest["status"], "advisory_success")
            self.assertTrue(manifest["delivery_advisory_used"])
            self.assertEqual(manifest["semantic_qc"]["post_final"]["failures"], ["subtitle_band_intrusion"])

    def test_pipeline_fails_fast_when_hero_model_is_missing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-pipeline-") as temp_root:
            root = Path(temp_root)
            runner = FakeRunner(root, with_hero_model=False)
            with self.assertRaises(WorkflowError):
                command_pipeline(runner, self.make_args())

            manifest = self.latest_pipeline_manifest(root)
            self.assertEqual(manifest["status"], "failed")
            self.assertIn("requires hero model", manifest["failure"])
            self.assertEqual(runner.render_calls, [])

    def test_opening_pipeline_uses_deterministic_composition_stage(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-opening-pipeline-") as temp_root:
            root = Path(temp_root)
            runner = FakeRunner(root)
            opening_artifact = (
                root
                / "output"
                / "cascadeeffects"
                / "scene_still"
                / "opening_culture_cluster"
                / "draft"
                / f"opening_seed_{BASE_SEED + 1}.png"
            )
            opening_artifact.parent.mkdir(parents=True, exist_ok=True)
            opening_artifact.write_text("opening", encoding="utf-8")
            compose_manifest = root / "runs" / "scene_still" / "opening_culture_cluster" / "opening_compose.run.json"
            compose_manifest.parent.mkdir(parents=True, exist_ok=True)
            compose_manifest.write_text("{}", encoding="utf-8")

            with mock.patch(
                "render_tool.compose_opening_tableau_draft",
                return_value={
                    "output_path": opening_artifact,
                    "run_manifest_path": compose_manifest,
                    "composition": {},
                },
            ):
                result = command_pipeline(runner, self.make_opening_args())

            self.assertEqual(result, 0)
            manifest = self.latest_pipeline_manifest(root, preset="opening_culture_cluster")
            self.assertEqual(manifest["selected_candidate"]["draft_stage"], "opening_tableau_compose")
            self.assertIn("opening_tableau_compose", manifest["stage_runs"])
            self.assertEqual(len([call for call in runner.render_calls if call[0] == "draft_txt2img"]), 0)
            self.assertEqual(len([call for call in runner.render_calls if call[0] == "refine_img2img"]), 0)
            self.assertEqual(len([call for call in runner.render_calls if call[0] == "final_upscale"]), 1)


if __name__ == "__main__":
    unittest.main()
