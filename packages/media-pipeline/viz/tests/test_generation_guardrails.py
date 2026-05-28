from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest import mock

try:
    from PIL import Image, ImageDraw
except ModuleNotFoundError:  # pragma: no cover - dependency varies by environment
    Image = None
    ImageDraw = None


ROOT = Path("/Users/mike/CascadeEffects/packages/media-pipeline/viz")
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from guardrail_policy import load_guardrail_policy, motion_guardrails_for  # noqa: E402
from guardrail_policy import semantic_qc_profile_for  # noqa: E402
from midjourney_package_tool import load_midjourney_package_shot  # noqa: E402

if Image is not None:
    from typography_tool import (  # noqa: E402
        audit_visual_qc_artifact,
        command_process_research_source,
        evaluate_semantic_qc_response,
        evaluate_visual_contract,
    )
else:  # pragma: no cover - dependency varies by environment
    audit_visual_qc_artifact = None
    command_process_research_source = None
    evaluate_semantic_qc_response = None
    evaluate_visual_contract = None
from render_tool import build_opening_tableau_layout, command_finalize_still, command_review_proof  # noqa: E402
from subject_reference_plate import SubjectReferencePlateError, load_plate_manifest  # noqa: E402
from workflow_tool import WorkflowCompiler, WorkflowError  # noqa: E402


def install_flux2_model_stubs(models_dir: Path) -> None:
    for directory_name, model_name in (
        ("diffusion_models", "flux2-dev.safetensors"),
        ("vae", "flux2-vae.safetensors"),
        ("text_encoders", "mistral_3_small_flux2_bf16.safetensors"),
        ("text_encoders", "clip_l.safetensors"),
        ("clip_vision", "clip_vision_g.safetensors"),
    ):
        target_dir = models_dir / directory_name
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / model_name).write_text("stub", encoding="utf-8")


class GenerationGuardrailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_guardrail_policy(ROOT)
        cls.compiler = WorkflowCompiler(
            repo_root=ROOT,
            models_root=ROOT / "tmp-models",
            comfy_workflows_dir=ROOT / "workflows" / "generated",
            comfy_output_dir=ROOT / "renders",
            references_root=ROOT / "references",
        )

    def test_packaging_prompt_guardrail_bans_scanline_cues(self) -> None:
        spec = {
            "family": "thumbnail_plate",
            "preset": "one_red_flag__draft_txt2img",
            "base_fragment": "flux_full_txt2img_base",
            "params": {
                "positive_prompt": "editorial collage",
            },
        }
        params = {
            "positive_prompt": (
                "editorial collage, torn paper, ripped seam, poster montage, anchor fragment, "
                "layered support fragments, recognizable anchor object, schematic overlay"
            ),
            "negative_prompt": (
                "no text, no words, no letters, no numbers, no digits, no labels, no stickers, "
                "no decals, no placards, no serial tags, no serial plates, no engraved plates, "
                "no warning signs, no warning plates, no stamped markings, no screen digits, "
                "no icon plates, no symbol plates, no interface readouts, no readable ui"
            ),
            "stage": "draft_txt2img",
        }
        with self.assertRaises(WorkflowError) as exc:
            self.compiler.validate_active_semantics(
                ROOT / "workflows/specs/thumbnail_plate/one_red_flag__draft_txt2img.json",
                spec,
                {},
                params,
            )
        self.assertIn("scanline-adjacent packaging cue", str(exc.exception))

    def test_visual_qc_scanline_guardrail_is_policy_driven(self) -> None:
        if Image is None or audit_visual_qc_artifact is None:
            self.skipTest("Pillow is not available in this environment.")
        image = Image.new("L", (256, 256))
        for row in range(256):
            value = 255 if row % 2 == 0 else 0
            for column in range(256):
                image.putpixel((column, row), value)
        rgba_image = image.convert("RGBA")

        relaxed_summary, _ = audit_visual_qc_artifact(rgba_image, ban_scanlines=False, debug_dir=None)
        enforced_summary, _ = audit_visual_qc_artifact(rgba_image, ban_scanlines=True, debug_dir=None)

        self.assertEqual(relaxed_summary["failures"], [])
        self.assertTrue(relaxed_summary["warnings"])
        self.assertTrue(enforced_summary["failures"])

    def test_zero_letter_prompt_bans_still_apply(self) -> None:
        spec = {
            "family": "shorts_scene_plate",
            "preset": "challenger_warning_cold__draft_txt2img",
            "base_fragment": "flux_full_txt2img_base",
            "params": {
                "positive_prompt": "editorial collage",
            },
        }
        params = {
            "positive_prompt": (
                "restrained evidence plate, one structural subject, quiet background, "
                "warning labels"
            ),
            "negative_prompt": (
                "no text, no words, no letters, no numbers, no digits, no labels, no stickers, "
                "no decals, no placards, no serial tags, no serial plates, no engraved plates, "
                "no warning signs, no warning plates, no stamped markings, no screen digits, "
                "no icon plates, no symbol plates, no interface readouts, no readable ui"
            ),
            "stage": "draft_txt2img",
        }
        with self.assertRaises(WorkflowError) as exc:
            self.compiler.validate_active_semantics(ROOT / "scene-test.json", spec, {}, params)
        self.assertIn("label-led active-image cue", str(exc.exception))

    def test_motion_policy_declares_minimum_duration(self) -> None:
        guardrails = motion_guardrails_for(
            self.policy,
            episode_id="therac-25",
            motion_item_id="console_alarm_push",
            preset_id="retired-scene-still/therac25_console_alarm",
        )
        self.assertEqual(guardrails["min_duration_seconds"], 0.0)

    def test_visual_research_reject_tags_include_source_text_unresolved(self) -> None:
        self.assertIn("source_text_unresolved", self.policy["gate_types"]["visual_research"])
        self.assertEqual(self.policy["reject_tags"]["source_text_unresolved"]["mode"], "machine_enforced")

    def test_scene_prompt_fragments_support_cap_is_enforced(self) -> None:
        with self.assertRaises(WorkflowError) as exc:
            self.compiler.validate_prompt_fragments(
                ROOT / "scene-test.json",
                "shorts_scene_plate",
                {
                    "anchor_fragment": "mission control anchor",
                    "support_fragments": ["support one", "support two", "support three"],
                },
            )
        self.assertIn("capped at 2 items", str(exc.exception))

    def test_semantic_qc_mapping_reuses_review_tags(self) -> None:
        if evaluate_semantic_qc_response is None:
            self.skipTest("Pillow is not available in this environment.")
        profile = semantic_qc_profile_for(
            self.policy,
            family="shorts_scene_plate",
            preset="challenger_warning_cold",
            profile_name="shorts_scene_default",
        )
        summary = evaluate_semantic_qc_response(
            {
                "anchor_recognition": "missing",
                "composition_score": 4.0,
                "clarity_score": 5.0,
                "issues": ["duplicate_human_identity"],
                "notes": "bad short beat plate",
            },
            profile,
            stage="candidate",
        )
        self.assertIn("duplicate_human_identity", summary["issues"])
        self.assertIn("unrecognizable_anchor", summary["issues"])
        self.assertTrue(summary["failures"])

    def test_scene_still_family_is_retired_from_active_workflow_surface(self) -> None:
        with self.assertRaises(WorkflowError) as exc:
            self.compiler.select_specs("scene_still")
        self.assertIn("retired", str(exc.exception))

    def test_active_workflow_list_excludes_retired_scene_still_family(self) -> None:
        active_families = {path.parent.name for path in self.compiler.list_specs(active_only=True)}
        self.assertNotIn("scene_still", active_families)

    def test_active_shorts_scene_build_uses_flux2_runtime_assets(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-models-") as models_root:
            models_dir = Path(models_root)
            install_flux2_model_stubs(models_dir)
            compiler = WorkflowCompiler(
                repo_root=ROOT,
                models_root=models_dir,
                comfy_workflows_dir=ROOT / "workflows" / "generated",
                comfy_output_dir=ROOT / "renders",
                references_root=ROOT / "references",
            )
            result = compiler.build_one(
                ROOT / "workflows/specs/shorts_scene_plate/challenger_warning_cold__draft_txt2img.json",
                write_generated=False,
                overrides={},
            )
        assets_by_kind = {
            asset["kind"]: asset
            for asset in result.manifest["dependency_report"]["assets"]
        }
        self.assertEqual(result.manifest["checkpoint"], "")
        self.assertEqual(result.params["full_unet_name"], "flux2-dev.safetensors")
        self.assertTrue(assets_by_kind["full_flux_unet"]["present"])
        self.assertTrue(assets_by_kind["full_flux_vae"]["present"])
        self.assertTrue(assets_by_kind["full_flux_text_encoder_primary"]["present"])
        self.assertTrue(assets_by_kind["full_flux_text_encoder_secondary"]["present"])
        self.assertNotIn("checkpoint", assets_by_kind)

    def test_retired_scene_still_profiles_are_not_active(self) -> None:
        profile = semantic_qc_profile_for(
            self.policy,
            family="scene_still",
            preset="opening_culture_cluster",
            profile_name="opening_culture_cluster",
        )
        self.assertEqual(profile["allowed_issue_tags"], [])
        self.assertEqual(profile["hard_fail_tags"], [])

    def test_hyatt_negative_prompt_includes_required_zero_letter_plate_terms(self) -> None:
        spec = json.loads(
            (ROOT / "workflows/specs/shorts_scene_plate/hyatt_accountability_chain__draft_txt2img.json").read_text(
                encoding="utf-8"
            )
        )
        negative_prompt = spec["params"]["negative_prompt"].lower()
        for phrase in ("no stickers", "no decals", "no placards", "no serial tags", "no serial plates"):
            self.assertIn(phrase, negative_prompt)

    def test_active_shorts_scene_semantic_profile_uses_active_gate_tags(self) -> None:
        profile = semantic_qc_profile_for(
            self.policy,
            family="shorts_scene_plate",
            preset="challenger_warning_cold",
            profile_name="shorts_scene_default",
        )
        self.assertIn("minimal-surreal short beats", profile["brief"].lower())
        self.assertIn("historical anchor", profile["stage_focus"]["candidate"].lower())
        self.assertTrue(set(profile["allowed_issue_tags"]).issubset(set(self.policy["gate_types"]["shorts_scene_plate"])))
        self.assertTrue(set(profile["hard_fail_tags"]).issubset(set(self.policy["gate_types"]["shorts_scene_plate"])))

    def test_active_shorts_scene_profile_prioritizes_single_portrait_read(self) -> None:
        profile = semantic_qc_profile_for(
            self.policy,
            family="shorts_scene_plate",
            preset="challenger_warning_cold",
            profile_name="shorts_scene_default",
        )
        self.assertIn("one primary read", profile["brief"].lower())
        self.assertIn("portrait candidate", profile["stage_focus"]["candidate"].lower())
        self.assertTrue(set(profile["allowed_issue_tags"]).issubset(set(self.policy["gate_types"]["shorts_scene_plate"])))
        self.assertTrue(set(profile["hard_fail_tags"]).issubset(set(self.policy["gate_types"]["shorts_scene_plate"])))

    def test_opening_tableau_layout_keeps_subject_centered_and_supports_peripheral(self) -> None:
        support_slots = [
            {"slot_id": "vhs_cassette"},
            {"slot_id": "boombox_radio"},
            {"slot_id": "high_top_sneaker"},
            {"slot_id": "aluminum_soda_can"},
            {"slot_id": "cube_puzzle"},
            {"slot_id": "beige_home_computer_crt"},
        ]
        layout = build_opening_tableau_layout(1344, 768, support_slots)
        subject = layout["subject"]
        self.assertGreater(subject["width"], 500)
        self.assertGreater(subject["height"], 500)
        self.assertLess(subject["x"], 500)
        self.assertGreater(subject["x"] + subject["width"], 800)
        self.assertEqual(len(layout["supports"]), 6)
        subject_right = subject["x"] + subject["width"]
        subject_bottom = subject["y"] + subject["height"]
        for support in layout["supports"]:
            support_right = support["x"] + support["width"]
            support_bottom = support["y"] + support["height"]
            overlaps_subject = not (
                support_right <= subject["x"]
                or support["x"] >= subject_right
                or support_bottom <= subject["y"]
                or support["y"] >= subject_bottom
            )
            self.assertFalse(overlaps_subject)

    def test_process_research_source_returns_clear_without_cleanup(self) -> None:
        if Image is None or command_process_research_source is None:
            self.skipTest("Pillow is not available in this environment.")
        with tempfile.TemporaryDirectory(prefix="ce-research-source-") as temp_dir:
            temp_root = Path(temp_dir)
            artifact_path = temp_root / "source.png"
            Image.new("RGBA", (64, 64), (240, 240, 240, 255)).save(artifact_path)
            stdout = io.StringIO()
            with mock.patch("sys.stdout", new=stdout):
                exit_code = command_process_research_source(
                    Namespace(
                        artifact=str(artifact_path),
                        policy=None,
                        output=str(temp_root / "cleaned.png"),
                        debug_dir=str(temp_root / "debug"),
                    )
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["status"], "clear")
            self.assertTrue(payload["text_detection_manifest_path"])

    def test_process_research_source_uses_cleanup_when_zero_letter_fails(self) -> None:
        if command_process_research_source is None:
            self.skipTest("Pillow is not available in this environment.")
        with tempfile.TemporaryDirectory(prefix="ce-research-source-") as temp_dir:
            temp_root = Path(temp_dir)
            artifact_path = temp_root / "source.png"
            policy_path = temp_root / "policy.json"
            output_path = temp_root / "cleaned.png"
            debug_dir = temp_root / "debug"
            artifact_path.write_text("stub", encoding="utf-8")
            policy_path.write_text(
                json.dumps(
                    {
                        "enabled": True,
                        "application_stage": "post_refine",
                        "surface_scope": "environmental_only",
                        "llm_backend": "ollama",
                        "llm_model": "llava:7b",
                        "allow_repaired_text_outside_typography_zones": False,
                        "ambiguous_environmental_fallback_action": "erase",
                        "max_regions": 8,
                        "ocr_confidence_floor": 60.0,
                        "rewrite_confidence_floor": 0.72,
                        "erase_confidence_floor": 0.58,
                        "context_terms": ["documentary source"],
                        "forbidden_surface_types": ["paperwork"],
                        "post_final_cleanup": {"enabled": True, "mode": "erase_only", "max_regions": 8},
                    }
                ),
                encoding="utf-8",
            )
            stdout = io.StringIO()
            with (
                mock.patch("sys.stdout", new=stdout),
                mock.patch("typography_tool.Image.open") as image_open,
                mock.patch(
                    "typography_tool.audit_zero_letter_artifact",
                    return_value=(
                        {
                            "status": "failed",
                            "unapproved_text": [{"text": "NASA"}],
                            "warnings": [],
                            "failures": ["Readable text detected."],
                        },
                        [],
                    ),
                ),
                mock.patch(
                    "typography_tool.cleanup_final_text_artifact",
                    return_value={
                        "cleanup_manifest_path": str(debug_dir / "cleanup_manifest.json"),
                        "output_artifact": str(output_path),
                        "debug_artifacts": [],
                        "residual_validation": {"status": "ok", "failures": []},
                    },
                ),
            ):
                image_open.return_value.convert.return_value = object()
                exit_code = command_process_research_source(
                    Namespace(
                        artifact=str(artifact_path),
                        policy=str(policy_path),
                        output=str(output_path),
                        debug_dir=str(debug_dir),
                    )
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["status"], "cleaned")
            self.assertEqual(payload["cleanup_manifest_path"], str(debug_dir / "cleanup_manifest.json"))

    def test_review_proof_stops_before_final_upscale(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-review-proof-") as temp_dir:
            temp_root = Path(temp_dir)
            draft_output = temp_root / "draft.png"
            refine_output = temp_root / "refine.png"
            candidate_manifest = temp_root / "candidate_qc.run.json"
            proof_manifest = temp_root / "proof_qc.run.json"
            draft_output.write_text("draft", encoding="utf-8")
            refine_output.write_text("refine", encoding="utf-8")
            candidate_manifest.write_text("{}", encoding="utf-8")
            proof_manifest.write_text("{}", encoding="utf-8")
            runner = mock.Mock()
            runner.server_url = "http://127.0.0.1:8188"
            runner.runs_root = temp_root / "runs"
            runner.models_root = temp_root / "models"
            runner.build_stage_result.return_value = Namespace(
                manifest={"pipeline_strategy": {"draft_candidate_count": 1, "seed_policy": "fixed", "semantic_qc_profile": "scene_default"}},
                params={"seed": 42, "selected_seed": 42},
            )
            runner.render_stage_once.side_effect = [
                {"run_manifest_path": temp_root / "draft.run.json", "output_files": [draft_output]},
                {"run_manifest_path": temp_root / "refine.run.json", "output_files": [refine_output]},
            ]
            runner.run_visual_qc_audit.side_effect = [
                {"status": "ok", "failures": [], "score": 0.95, "threshold": 0.8, "semantic": {"ranking_score": 0.7}},
                {"status": "ok", "failures": [], "score": 0.97, "threshold": 0.8, "semantic": {"ranking_score": 0.9}},
            ]
            runner.write_visual_qc_run_manifest.side_effect = [candidate_manifest, proof_manifest]
            runner.relative_output_path.return_value = "draft.png"

            stdout = io.StringIO()
            with mock.patch("sys.stdout", new=stdout):
                exit_code = command_review_proof(
                    runner,
                    Namespace(
                        family="scene_still",
                        preset="challenger_launch_exterior",
                        selected_seed=42,
                        overrides=[],
                        quality_profile="standard",
                        delivery_mode="strict",
                    ),
                )

            self.assertEqual(exit_code, 0)
            manifest_path = next((runner.runs_root / "scene_still" / "challenger_launch_exterior").glob("*__review_proof.run.json"))
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["final_outputs"], [str(refine_output)])
            self.assertNotIn("final_upscale", manifest["stage_runs"])
            self.assertNotIn("cleanup_final_text", manifest["stage_runs"])
            self.assertEqual(manifest["stage_runs"]["refine_img2img"], str(temp_root / "refine.run.json"))
            self.assertEqual(manifest["stage_validations"]["visual_qc"]["artifact_path"], str(refine_output))
            self.assertIn("INFO  pipeline manifest ->", stdout.getvalue())

    def test_finalize_still_runs_finishing_from_existing_proof(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-finalize-still-") as temp_dir:
            temp_root = Path(temp_dir)
            source_image = temp_root / "review_approved.png"
            final_output = temp_root / "final.png"
            repaired_output = temp_root / "review_approved__repair.png"
            cleaned_output = temp_root / "final__cleaned.png"
            repair_manifest = temp_root / "repair.run.json"
            cleanup_manifest = temp_root / "cleanup.run.json"
            cleanup_audit_manifest = temp_root / "cleanup_audit.run.json"
            visual_qc_manifest = temp_root / "visual_qc.run.json"
            zero_letter_manifest = temp_root / "zero_letter.run.json"
            source_image.write_text("source", encoding="utf-8")
            final_output.write_text("final", encoding="utf-8")
            repaired_output.write_text("repair", encoding="utf-8")
            cleaned_output.write_text("clean", encoding="utf-8")
            for path in (repair_manifest, cleanup_manifest, cleanup_audit_manifest, visual_qc_manifest, zero_letter_manifest):
                path.write_text("{}", encoding="utf-8")

            runner = mock.Mock()
            runner.server_url = "http://127.0.0.1:8188"
            runner.runs_root = temp_root / "runs"
            runner.models_root = temp_root / "models"
            runner.build_stage_result.return_value = Namespace(
                manifest={"pipeline_strategy": {"draft_candidate_count": 2, "seed_policy": "search", "semantic_qc_profile": "scene_default"}},
                params={"seed": 77, "selected_seed": 77},
            )
            runner.repair_policy_should_run.return_value = (
                True,
                (
                    temp_root / "policy.json",
                    {"enabled": True, "post_final_cleanup": {"enabled": True}},
                ),
            )
            runner.render_stage_once.return_value = {
                "run_manifest_path": temp_root / "final.run.json",
                "output_files": [final_output],
            }
            runner.run_source_text_repair.return_value = {"output_artifact": str(repaired_output)}
            runner.write_repair_run_manifest.return_value = repair_manifest
            runner.typography_should_run.return_value = (False, None)
            runner.run_cleanup_final_text.return_value = {
                "cleanup_manifest_path": str(temp_root / "cleanup_manifest.json"),
                "output_artifact": str(cleaned_output),
                "residual_validation": {"status": "ok", "failures": []},
            }
            runner.write_cleanup_run_manifest.return_value = cleanup_manifest
            runner.write_cleanup_text_audit_run_manifest.return_value = cleanup_audit_manifest
            runner.run_visual_qc_audit.return_value = {
                "status": "ok",
                "failures": [],
                "score": 0.98,
                "threshold": 0.8,
                "semantic": {"ranking_score": 0.0},
            }
            runner.write_visual_qc_run_manifest.return_value = visual_qc_manifest
            runner.run_zero_letter_audit.return_value = {"status": "ok", "failures": [], "warnings": [], "unapproved_text": []}
            runner.write_zero_letter_audit_run_manifest.return_value = zero_letter_manifest

            stdout = io.StringIO()
            with mock.patch("sys.stdout", new=stdout):
                exit_code = command_finalize_still(
                    runner,
                    Namespace(
                        family="scene_still",
                        preset="challenger_launch_exterior",
                        source_image=str(source_image),
                        selected_seed=77,
                        overrides=[],
                        typography="off",
                        source_text_repair="auto",
                        quality_profile="standard",
                        delivery_mode="strict",
                    ),
                )

            self.assertEqual(exit_code, 0)
            manifest_path = next((runner.runs_root / "scene_still" / "challenger_launch_exterior").glob("*__finalize_still.run.json"))
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertNotIn("draft_txt2img", manifest["stage_runs"])
            self.assertNotIn("refine_img2img", manifest["stage_runs"])
            self.assertEqual(manifest["stage_runs"]["final_upscale"], str(temp_root / "final.run.json"))
            self.assertEqual(manifest["stage_runs"]["repair_source_text"], str(repair_manifest))
            self.assertEqual(manifest["stage_runs"]["cleanup_final_text"], str(cleanup_manifest))
            self.assertEqual(manifest["final_outputs"], [str(cleaned_output)])
            self.assertEqual(manifest["selected_candidate"]["source_image"], str(source_image.resolve()))
            self.assertIn("INFO  pipeline manifest ->", stdout.getvalue())

    def test_minimal_surreal_shorts_scene_build_preserves_contract_prompting(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-models-") as models_root:
            models_dir = Path(models_root)
            install_flux2_model_stubs(models_dir)
            compiler = WorkflowCompiler(
                repo_root=ROOT,
                models_root=models_dir,
                comfy_workflows_dir=ROOT / "workflows" / "generated",
                comfy_output_dir=ROOT / "renders",
                references_root=ROOT / "references",
                comfy_clip_vision_model="clip_vision_g.safetensors",
            )
            shot = load_midjourney_package_shot(
                "references/episodes/challenger/shorts/midjourney/challenger_short_minimal_surreal_v1/package.manifest.json",
                shot_id="beat_01",
                repo_root=ROOT,
            )
            result = compiler.build_one(
                ROOT / "workflows/specs/shorts_scene_plate/challenger_warning_cold__draft_txt2img.json",
                write_generated=False,
                overrides={},
            )
        self.assertEqual(result.manifest["style_profile"], "minimal_surreal_editorial")
        self.assertEqual(result.manifest["beat_id"], "beat_01")
        self.assertEqual(result.manifest["pipeline_strategy"]["draft_candidate_count"], 4)
        self.assertTrue(result.manifest["midjourney_package"]["active"])
        self.assertEqual(
            result.manifest["midjourney_package"]["package_id"],
            "challenger_short_minimal_surreal_v1__midjourney_v1",
        )
        self.assertEqual(result.manifest["midjourney_package"]["shot_id"], "beat_01")
        self.assertEqual(result.manifest["midjourney_package"]["reference_files"], list(shot.reference_files))
        self.assertIn(shot.prompt_text, result.manifest["prompt"])
        self.assertIn(
            "favor icicle-heavy pipe detail, winter haze, and cold-risk infrastructure signal over a full tower or roadway scene",
            result.manifest["prompt"],
        )
        self.assertIn("one cold-risk infrastructure signal dominated by icicle-heavy pipe detail and winter haze", result.manifest["prompt"])
        self.assertIn("caption-safe keep-out zones", result.manifest["prompt"])
        self.assertIn("negative space occupies at least 60% of the frame", result.manifest["prompt"])
        self.assertIn("ordered reference grid is guidance only", result.manifest["prompt"])
        self.assertNotIn("historical anchor:", result.manifest["prompt"])
        self.assertNotIn("surreal breach:", result.manifest["prompt"])
        self.assertIn(
            "no watermark",
            result.manifest["negative_prompt"],
        )
        self.assertIn(
            "no shuttle stack",
            result.manifest["negative_prompt"],
        )
        self.assertIn(
            "no tower hero",
            result.manifest["negative_prompt"],
        )
        self.assertIn(
            "center-weighted composition",
            result.manifest["negative_prompt"],
        )
        self.assertEqual(
            result.manifest["style_contract"]["caption_safe_defaults"]["subtitles"],
            [0.08, 0.74, 0.92, 0.96],
        )
        self.assertEqual(result.manifest["subject_reference"]["clip_vision_model"], "clip_vision_g.safetensors")
        self.assertEqual(
            result.manifest["subject_reference"]["source_path"],
            "cascadeeffects/midjourney_package_grids/shorts_scene_plate/challenger_warning_cold/beat_01__reference_grid.png",
        )
        self.assertFalse(result.manifest["plate_seed"]["active"])
        self.assertFalse(result.manifest["composition_control"]["active"])
        self.assertFalse(result.manifest["palette_lock"]["active"])
        self.assertFalse(result.manifest["spatial_mask"]["active"])
        self.assertTrue(result.manifest["midjourney_package"]["adapter"]["active"])
        self.assertEqual(
            result.manifest["midjourney_package"]["adapter"]["grid_layout_template"],
            "detail_left_bias_triptych",
        )
        self.assertEqual(
            result.manifest["midjourney_package"]["adapter"]["steer_target"],
            "cold_pipe_winter_signal",
        )
        self.assertEqual(
            result.manifest["midjourney_package"]["adapter"]["ranking_bias_tags"],
            ["cold_pipe_detail", "winter_haze", "industrial_frost_signal"],
        )
        self.assertEqual(
            result.manifest["midjourney_package"]["adapter"]["included_reference_indices"],
            [1, 0, 2],
        )
        self.assertEqual(
            result.manifest["style_contract"]["plate_seed_defaults"]["draft_denoise"],
            0.5,
        )
        class_types = {node["class_type"] for node in result.prompt.values()}
        self.assertIn("LoadImage", class_types)
        self.assertIn("EmptySD3LatentImage", class_types)
        self.assertIn("CLIPVisionLoader", class_types)
        self.assertIn("CLIPVisionEncode", class_types)
        self.assertIn("unCLIPConditioning", class_types)
        self.assertNotIn("ConditioningSetMask", class_types)
        self.assertNotIn("SetLatentNoiseMask", class_types)
        self.assertNotIn("VAEEncode", class_types)
        load_image_inputs = [
            node["inputs"] for node in result.prompt.values() if node["class_type"] == "LoadImage"
        ]
        self.assertEqual(len(load_image_inputs), 1)
        self.assertEqual(
            load_image_inputs[0]["image"],
            "cascadeeffects/midjourney_package_grids/shorts_scene_plate/challenger_warning_cold/beat_01__reference_grid.png [input]",
        )

    def test_minimal_surreal_requires_midjourney_package_for_package_grid_mode(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-models-") as models_root:
            models_dir = Path(models_root)
            install_flux2_model_stubs(models_dir)
            compiler = WorkflowCompiler(
                repo_root=ROOT,
                models_root=models_dir,
                comfy_workflows_dir=ROOT / "workflows" / "generated",
                comfy_output_dir=ROOT / "renders",
                references_root=ROOT / "references",
                comfy_clip_vision_model="clip_vision_g.safetensors",
            )
            with self.assertRaises(WorkflowError) as exc:
                compiler.build_one(
                    ROOT / "workflows/specs/shorts_scene_plate/challenger_warning_cold__draft_txt2img.json",
                    write_generated=False,
                    overrides={"midjourney_package_path": ""},
                )
        self.assertIn("midjourney_package_path", str(exc.exception))

    def test_minimal_surreal_allows_runtime_subject_reference_overrides(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ce-models-") as models_root:
            models_dir = Path(models_root)
            install_flux2_model_stubs(models_dir)
            compiler = WorkflowCompiler(
                repo_root=ROOT,
                models_root=models_dir,
                comfy_workflows_dir=ROOT / "workflows" / "generated",
                comfy_output_dir=ROOT / "renders",
                references_root=ROOT / "references",
                comfy_clip_vision_model="clip_vision_g.safetensors",
            )
            result = compiler.build_one(
                ROOT / "workflows/specs/shorts_cover_plate/challenger_thesis_cover__draft_txt2img.json",
                write_generated=False,
                overrides={
                    "subject_reference_runtime_image": (
                        "cascadeeffects/midjourney_package_grids/shorts_cover_plate/challenger_thesis_cover/"
                        "cover__reference_grid.png"
                    ),
                    "subject_reference_clip_vision_model": "clip_vision_g.safetensors",
                },
            )
            refine_result = compiler.build_one(
                ROOT / "workflows/specs/shorts_cover_plate/challenger_thesis_cover__refine_img2img.json",
                write_generated=False,
                overrides={
                    "subject_reference_runtime_image": (
                        "cascadeeffects/midjourney_package_grids/shorts_cover_plate/challenger_thesis_cover/"
                        "cover__reference_grid.png"
                    ),
                    "subject_reference_clip_vision_model": "clip_vision_g.safetensors",
                    "source_image": (
                        "cascadeeffects/shorts_cover_plate/challenger_thesis_cover/draft/"
                        "challenger_thesis_cover_draft_00001_.png"
                    ),
                },
            )
        load_image_inputs = next(node["inputs"] for node in result.prompt.values() if node["class_type"] == "LoadImage")
        self.assertEqual(
            load_image_inputs["image"],
            "cascadeeffects/midjourney_package_grids/shorts_cover_plate/challenger_thesis_cover/cover__reference_grid.png [input]",
        )
        refine_load_image_inputs = next(
            node["inputs"] for node in refine_result.prompt.values() if node["class_type"] == "LoadImage"
        )
        self.assertEqual(
            refine_load_image_inputs["image"],
            "cascadeeffects/midjourney_package_grids/shorts_cover_plate/challenger_thesis_cover/cover__reference_grid.png [input]",
        )
        clip_loader_inputs = next(
            node["inputs"] for node in result.prompt.values() if node["class_type"] == "CLIPVisionLoader"
        )
        self.assertEqual(clip_loader_inputs["clip_name"], "clip_vision_g.safetensors")
        self.assertTrue(result.manifest["midjourney_package"]["active"])
        self.assertTrue(result.manifest["midjourney_package"]["adapter"]["active"])
        self.assertFalse(result.manifest["composition_control"]["active"])
        self.assertFalse(result.manifest["palette_lock"]["active"])

    def test_widget_normalization_uses_input_suffix_for_load_image(self) -> None:
        self.assertEqual(
            WorkflowCompiler.normalize_widget_value("LoadImage", "image", "cascadeeffects/refs/hero.png"),
            "cascadeeffects/refs/hero.png [input]",
        )
        self.assertEqual(
            WorkflowCompiler.normalize_widget_value("LoadImageOutput", "image", "cascadeeffects/output/hero.png"),
            "cascadeeffects/output/hero.png [output]",
        )

    def test_shorts_scene_validation_rejects_invalid_caption_safe_zone(self) -> None:
        spec = json.loads(
            (ROOT / "workflows/specs/shorts_scene_plate/challenger_warning_cold__draft_txt2img.json").read_text(
                encoding="utf-8"
            )
        )
        path = ROOT / "workflows/specs/shorts_scene_plate/challenger_invalid_zone__draft_txt2img.json"
        spec["preset"] = path.stem
        spec["params"]["caption_safe_zone"] = {
            "top_ui": [0.0, 0.0, 1.0, 0.12],
            "subtitles": [0.92, 0.74, 0.08, 0.96],
        }
        with self.assertRaises(WorkflowError) as exc:
            self.compiler.validate_spec_shape(spec, path)
        self.assertIn("positive-area box", str(exc.exception))

    def test_minimal_surreal_requires_midjourney_shot_id_for_package_grid_mode(self) -> None:
        spec_path = ROOT / "workflows/specs/shorts_scene_plate/challenger_warning_cold__draft_txt2img.json"
        with tempfile.TemporaryDirectory(prefix="ce-models-") as models_root:
            models_dir = Path(models_root)
            install_flux2_model_stubs(models_dir)
            compiler = WorkflowCompiler(
                repo_root=ROOT,
                models_root=models_dir,
                comfy_workflows_dir=ROOT / "workflows" / "generated",
                comfy_output_dir=ROOT / "renders",
                references_root=ROOT / "references",
                comfy_clip_vision_model="clip_vision_g.safetensors",
            )
            with self.assertRaises(WorkflowError) as exc:
                compiler.build_one(
                    spec_path,
                    write_generated=False,
                    overrides={
                        "midjourney_shot_id": ""
                    },
                )
        self.assertIn("midjourney_shot_id", str(exc.exception))

    def test_minimal_surreal_rejects_missing_midjourney_adapter_path(self) -> None:
        spec_path = ROOT / "workflows/specs/shorts_scene_plate/challenger_warning_cold__draft_txt2img.json"
        with tempfile.TemporaryDirectory(prefix="ce-models-") as models_root:
            models_dir = Path(models_root)
            install_flux2_model_stubs(models_dir)
            compiler = WorkflowCompiler(
                repo_root=ROOT,
                models_root=models_dir,
                comfy_workflows_dir=ROOT / "workflows" / "generated",
                comfy_output_dir=ROOT / "renders",
                references_root=ROOT / "references",
                comfy_clip_vision_model="clip_vision_g.safetensors",
            )
            with self.assertRaises(WorkflowError) as exc:
                compiler.build_one(
                    spec_path,
                    write_generated=False,
                    overrides={
                        "midjourney_adapter_path": "references/episodes/challenger/shorts/midjourney/challenger_short_minimal_surreal_v1/comfy_adapters/missing.json"
                    },
                )
        self.assertIn("missing.json", str(exc.exception))

    def test_challenger_plate_manifest_rejects_allow_humans(self) -> None:
        manifest_path = ROOT / "references/episodes/challenger/subject_reference_plates/manifests/challenger_warning_cold.json"
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        payload["allow_humans"] = True
        with tempfile.TemporaryDirectory(prefix="ce-plate-manifest-") as temp_root:
            temp_manifest = Path(temp_root) / "challenger_warning_cold.json"
            temp_manifest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            with self.assertRaises(SubjectReferencePlateError) as exc:
                load_plate_manifest(temp_manifest, episode_id="challenger")
        self.assertIn("allow_humans must stay false", str(exc.exception))

    def minimal_surreal_contract(self) -> dict[str, object]:
        profile = json.loads(
            (ROOT / "workflows/style_profiles/minimal_surreal_editorial.json").read_text(encoding="utf-8")
        )
        return {
            "style_id": profile["name"],
            "contract_metrics": profile["contract_metrics"],
            "caption_safe_defaults": profile["caption_safe_defaults"],
        }

    def minimal_surreal_image(self, *, centered: bool = False, subtitle_intrusion: bool = False) -> object:
        if Image is None or ImageDraw is None:
            self.skipTest("Pillow is not available in this environment.")
        image = Image.new("RGB", (400, 700), (238, 234, 226))
        draw = ImageDraw.Draw(image)
        left = 150 if centered else 40
        right = 250 if centered else 140
        top = 520 if subtitle_intrusion else 120
        bottom = 680 if subtitle_intrusion else 460
        draw.rectangle((left, top, right, bottom), fill=(38, 45, 56))
        draw.rectangle((right - 14, top + 136, right + 14, top + 198), fill=(228, 46, 46))
        return image

    def test_visual_contract_passes_for_off_center_single_accent_frame(self) -> None:
        if evaluate_visual_contract is None:
            self.skipTest("Pillow is not available in this environment.")
        summary = evaluate_visual_contract(
            self.minimal_surreal_image(),
            contract_config=self.minimal_surreal_contract(),
        )
        self.assertTrue(summary["pass"])
        self.assertEqual(summary["failures"], [])

    def test_visual_contract_rejects_center_weighted_subject(self) -> None:
        if evaluate_visual_contract is None:
            self.skipTest("Pillow is not available in this environment.")
        summary = evaluate_visual_contract(
            self.minimal_surreal_image(centered=True),
            contract_config=self.minimal_surreal_contract(),
        )
        self.assertIn("center_weighted_primary_subject", summary["failures"])

    def test_visual_contract_rejects_multiple_accents(self) -> None:
        if evaluate_visual_contract is None or ImageDraw is None:
            self.skipTest("Pillow is not available in this environment.")
        image = self.minimal_surreal_image()
        draw = ImageDraw.Draw(image)
        draw.rectangle((70, 500, 92, 538), fill=(40, 220, 70))
        summary = evaluate_visual_contract(
            image,
            contract_config=self.minimal_surreal_contract(),
        )
        self.assertIn("more_than_one_saturated_accent", summary["failures"])

    def test_visual_contract_rejects_high_symmetry(self) -> None:
        if evaluate_visual_contract is None or ImageDraw is None:
            self.skipTest("Pillow is not available in this environment.")
        image = Image.new("RGB", (400, 700), (238, 234, 226))
        draw = ImageDraw.Draw(image)
        draw.rectangle((60, 140, 140, 500), fill=(38, 45, 56))
        draw.rectangle((260, 140, 340, 500), fill=(38, 45, 56))
        summary = evaluate_visual_contract(
            image,
            contract_config=self.minimal_surreal_contract(),
        )
        self.assertIn("symmetry_too_high", summary["failures"])

    def test_visual_contract_rejects_subtitle_band_intrusion(self) -> None:
        if evaluate_visual_contract is None:
            self.skipTest("Pillow is not available in this environment.")
        summary = evaluate_visual_contract(
            self.minimal_surreal_image(subtitle_intrusion=True),
            contract_config=self.minimal_surreal_contract(),
        )
        self.assertIn("subtitle_band_intrusion", summary["failures"])

    def test_visual_contract_rejects_control_asset_leakage(self) -> None:
        if evaluate_visual_contract is None:
            self.skipTest("Pillow is not available in this environment.")
        with tempfile.TemporaryDirectory(prefix="ce-control-leak-") as temp_root:
            preview_path = Path(temp_root) / "preview.png"
            preview = self.minimal_surreal_image()
            preview.save(preview_path)
            contract = self.minimal_surreal_contract()
            contract["composition_control"] = {
                "active": True,
                "preview_path": str(preview_path),
            }
            summary = evaluate_visual_contract(preview, contract_config=contract)
        self.assertIn("control_asset_leakage", summary["failures"])


if __name__ == "__main__":
    unittest.main()
