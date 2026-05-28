from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image, ImageChops


ROOT = Path("/Users/mike/Viz_CascadeEffects")
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from house_crt_static_final_pass import (  # noqa: E402
    CALIBRATION_RECIPE_ID,
    CORRECTED_PASS_ID,
    FIRST_EIGHT_TARGET_ORDER,
    HOUSE_CRT_CONTRACT_ID,
    HOUSE_CRT_INTENSITY,
    HOUSE_CRT_PROFILE_ID,
    HOUSE_CRT_TONE_POLICY,
    LEGACY_CALIBRATION_RECIPE_ID,
    LUMA_YAVG_TOLERANCE,
    SIGNAL_INTERRUPTION_DURATION_SECONDS,
    SIGNAL_INTERRUPTION_PROFILE_ID,
    STATIC_DURATION_SECONDS,
    STATIC_PROFILE_ID,
    TEXTURE_RENDERER_SOURCE,
    VISIBLE_SCANLINE_CALIBRATION_PASS_ID,
    VISIBLE_SCANLINE_CALIBRATION_RECIPE_ID,
    VISIBLE_SCANLINE_FULL_PASS_ID,
    VISIBLE_SCANLINE_HIGH_VISIBILITY_LADDER_PASS_ID,
    VISIBLE_SCANLINE_HIGH_VISIBILITY_VARIANTS,
    VISIBLE_SCANLINE_SELECTED_STRENGTH_VARIANT_ID,
    VISIBLE_SCANLINE_DELTA_RGB,
    VISIBLE_SCANLINE_POLICY_ID,
    VISIBLE_SCANLINE_RENDERER_SOURCE,
    VISIBLE_SCANLINE_STRENGTH_LADDER_PASS_ID,
    VISIBLE_SCANLINE_STRENGTH_VARIANTS,
    VISIBLE_SCANLINE_TONE_POLICY,
    apply_signal_frame,
    contract_read,
    discover_current_final_manifests,
    extract_rows,
    find_caption_ass_path,
    find_final_path,
    historical_signal_filter_graph,
    luma_neutral_chroma_visible_scanline_filter_graph,
    scanline_visibility_from_image,
    selected_visible_scanline_variant,
    summarize_scanline_strength_ladder,
    texture_metric_read,
    visible_scanline_contract_read,
    normalize_segments,
    resolve_clean_source_plan,
    resolve_first_eight_final_manifests,
    resolve_segment_source_rows,
    resolve_source_proof,
    row_start_end,
    source_manifest_pretextured_reasons,
    source_path_is_pretextured,
    visual_layer_order_read,
)


class HouseCrtStaticFinalPassTests(unittest.TestCase):
    def test_active_final_caption_and_final_paths_support_standard_and_output_shapes(self) -> None:
        standard = {
            "captioned_final_path": "/tmp/current_final.mp4",
            "caption_ass_path": "/tmp/current_captions.ass",
        }
        nested = {
            "outputs": {
                "captioned_final_path": "/tmp/nested_final.mp4",
                "caption_ass_path": "/tmp/nested_captions.ass",
            }
        }

        self.assertEqual(find_final_path(standard), Path("/tmp/current_final.mp4"))
        self.assertEqual(find_caption_ass_path(standard), Path("/tmp/current_captions.ass"))
        self.assertEqual(find_final_path(nested), Path("/tmp/nested_final.mp4"))
        self.assertEqual(find_caption_ass_path(nested), Path("/tmp/nested_captions.ass"))

    def test_resolve_source_proof_recurses_through_prior_final_export_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            proof = temp / "proof.json"
            upstream = temp / "upstream_final_export.json"
            proof.write_text("{}", encoding="utf-8")
            upstream.write_text(json.dumps({"source_proof_manifest_path": str(proof)}), encoding="utf-8")

            resolved = resolve_source_proof("fixture", {"source_final_export_manifest_path": str(upstream)})

        self.assertEqual(resolved, proof)

    def test_extract_rows_supports_inline_and_external_edl_rows(self) -> None:
        inline = {"beats": [{"cue_start_seconds": 0.0, "cue_end_seconds": 1.0}]}
        self.assertEqual(extract_rows(inline), inline["beats"])

        with tempfile.TemporaryDirectory() as temp_dir:
            edl_path = Path(temp_dir) / "edl.json"
            edl_rows = [{"row_id": "edl_01", "timeline_in": 0.0, "timeline_out": 1.25}]
            edl_path.write_text(json.dumps({"rows": edl_rows}), encoding="utf-8")

            self.assertEqual(extract_rows({"shot_timing_edl_path": str(edl_path)}), edl_rows)

    def test_normalize_segments_accepts_active_final_timing_field_variants(self) -> None:
        rows = [
            {"row_id": "edl_01", "timeline_in": 0.0, "timeline_out": 2.0},
            {"id": "beat_02", "cue_start_seconds": 2.0, "cue_end_seconds": 4.5},
            {"shot_id": "shot_03", "proof_start": 4.5, "proof_end": 6.0},
            {"row_id": "too_short", "start_seconds": 6.0, "duration_seconds": 0.02},
        ]

        self.assertEqual(row_start_end(rows[1]), (2.0, 4.5))
        segments = normalize_segments(rows, visual_duration=10.0)

        self.assertEqual([segment.source_row_id for segment in segments], ["edl_01", "beat_02", "shot_03"])
        self.assertEqual([round(segment.duration, 3) for segment in segments], [2.0, 2.5, 1.5])

    def test_segment_source_rows_support_ordered_no_caption_clip_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            clip_1 = root / "clip_1.mp4"
            clip_2 = root / "clip_2.mp4"
            clip_1.write_text("clip", encoding="utf-8")
            clip_2.write_text("clip", encoding="utf-8")
            manifest = {
                "segments": [
                    {"row_id": "edl_01", "source_motion_clip_path": str(clip_1)},
                    {"edl_id": "edl_02", "source_motion_clip_path": str(clip_2)},
                ]
            }

            with mock.patch("house_crt_static_final_pass.duration", side_effect=[2.5, 3.0]):
                rows = resolve_segment_source_rows(manifest)

        self.assertEqual([row[0].source_row_id for row in rows], ["edl_01", "edl_02"])
        self.assertEqual([round(row[2], 3) for row in rows], [0.0, 2.5])
        self.assertEqual([round(row[3], 3) for row in rows], [2.5, 5.5])

    def test_house_crt_static_constants_match_active_final_rebuild_policy(self) -> None:
        self.assertEqual(CORRECTED_PASS_ID, "house_crt_clean_source_lineage_first8_pass_06")
        self.assertEqual(HOUSE_CRT_CONTRACT_ID, "house_crt_luma_neutral_chroma_signal_interruption_v1")
        self.assertEqual(HOUSE_CRT_PROFILE_ID, "era_1980s_broadcast_crt_v1")
        self.assertEqual(HOUSE_CRT_INTENSITY, "visible_but_premium")
        self.assertEqual(HOUSE_CRT_TONE_POLICY, "luma_neutral_chroma_v1")
        self.assertEqual(CALIBRATION_RECIPE_ID, "premium_broadcast_crt_luma_neutral_chroma_v1")
        self.assertEqual(LEGACY_CALIBRATION_RECIPE_ID, "premium_broadcast_crt_luma_neutral_chroma_v1")
        self.assertEqual(TEXTURE_RENDERER_SOURCE, "house_crt_static_final_pass.luma_neutral_chroma_filter_graph")
        self.assertEqual(STATIC_PROFILE_ID, "era_1980s_horizontal_signal_interruption_v2_randomized")
        self.assertEqual(STATIC_DURATION_SECONDS, 0.25)

    def test_first_eight_resolver_returns_exact_series_bible_targets(self) -> None:
        resolved = resolve_first_eight_final_manifests()
        self.assertEqual([target for target, _path in resolved], list(FIRST_EIGHT_TARGET_ORDER))
        self.assertEqual(
            set(FIRST_EIGHT_TARGET_ORDER),
            {"challenger", "therac-25", "hyatt", "tacoma", "semmelweis", "piltdown", "titanic", "737-max"},
        )
        self.assertIn("challenger", [target for target, _path in resolved])

    def test_current_final_resolver_supports_generic_future_episode_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            final_manifest = root / "future_final_export.json"
            final_manifest.write_text("{}", encoding="utf-8")
            episode_toml = root / "future-short.toml"
            episode_toml.write_text(
                "\n".join(
                    [
                        'id = "future-short"',
                        f'final_export_manifest_path = "{final_manifest}"',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            self.assertEqual(discover_current_final_manifests(root), [("future-short", final_manifest)])

    def test_contract_and_layer_order_are_episode_agnostic_and_caption_last(self) -> None:
        read = contract_read()
        layer_read = visual_layer_order_read()

        self.assertEqual(read["house_crt_contract_id"], HOUSE_CRT_CONTRACT_ID)
        self.assertEqual(read["renderer_scope"], "episode_agnostic_house_contract")
        self.assertFalse(read["episode_specific_texture_branch_allowed"])
        self.assertTrue(layer_read["caption_burn_is_last_visual_operation"])
        self.assertFalse(layer_read["post_caption_visual_effects_applied"])
        self.assertIn("caption_burn_last_visual_layer", layer_read["visual_layer_sequence"])

    def test_house_crt_uses_luma_neutral_chroma_graph_not_old_darkening_graph(self) -> None:
        graph = historical_signal_filter_graph(
            profile_id=HOUSE_CRT_PROFILE_ID,
            strength=HOUSE_CRT_INTENSITY,
            width=1080,
            height=1920,
            fps=30.0,
        )

        self.assertIn("crop=1079:1919:0.5+0.5*sin(n/17):0.5+0.5*cos(n/19)", graph)
        self.assertIn("saturation=1.280", graph)
        self.assertIn("noise=c0s=", graph)
        self.assertNotIn("saturation=0.960", graph)
        self.assertNotIn("geq=r='0':g='0':b='0':a='if(eq(mod(Y,4),0),8,0)'", graph)
        self.assertNotIn("drawgrid", graph)
        self.assertNotIn("vignette", graph)

    def test_visible_scanline_contract_records_policy_and_renderer(self) -> None:
        read = visible_scanline_contract_read()

        self.assertEqual(VISIBLE_SCANLINE_CALIBRATION_PASS_ID, "house_crt_visible_scanline_calibration_pass_07a")
        self.assertEqual(VISIBLE_SCANLINE_STRENGTH_LADDER_PASS_ID, "house_crt_visible_scanline_strength_ladder_pass_07b")
        self.assertEqual(
            VISIBLE_SCANLINE_HIGH_VISIBILITY_LADDER_PASS_ID,
            "house_crt_visible_scanline_high_visibility_ladder_pass_07c",
        )
        self.assertEqual(read["texture_tone_policy"], VISIBLE_SCANLINE_TONE_POLICY)
        self.assertEqual(read["calibration_recipe_id"], VISIBLE_SCANLINE_CALIBRATION_RECIPE_ID)
        self.assertEqual(read["scanline_policy_id"], VISIBLE_SCANLINE_POLICY_ID)
        self.assertEqual(read["texture_renderer_source"], VISIBLE_SCANLINE_RENDERER_SOURCE)
        self.assertEqual(read["full_first8_pass_id_after_review"], VISIBLE_SCANLINE_FULL_PASS_ID)
        self.assertEqual(read["strength_ladder_pass_id"], VISIBLE_SCANLINE_STRENGTH_LADDER_PASS_ID)
        self.assertEqual(read["high_visibility_ladder_pass_id"], VISIBLE_SCANLINE_HIGH_VISIBILITY_LADDER_PASS_ID)
        self.assertEqual(read["selected_scanline_strength_variant_id"], VISIBLE_SCANLINE_SELECTED_STRENGTH_VARIANT_ID)
        self.assertFalse(read["black_only_scanline_overlay_used"])
        self.assertTrue(read["zero_mean_horizontal_modulation"])

    def test_visible_scanline_graph_uses_zero_mean_modulation_not_black_overlay(self) -> None:
        graph = luma_neutral_chroma_visible_scanline_filter_graph(
            profile_id=HOUSE_CRT_PROFILE_ID,
            strength=HOUSE_CRT_INTENSITY,
            width=1080,
            height=1920,
            fps=30.0,
        )

        self.assertIn("format=yuv444p", graph)
        self.assertIn("geq=lum=", graph)
        self.assertIn("mod(Y,4)", graph)
        self.assertIn(",-6.000", graph)
        self.assertIn(",6.000", graph)
        self.assertIn("cb='cb(X,Y)':cr='cr(X,Y)'", graph)
        self.assertNotIn("color=c=black", graph)
        self.assertNotIn("[scan]overlay", graph)
        self.assertNotIn("saturation=0.960", graph)

    def test_visible_scanline_graph_supports_exact_variant_delta(self) -> None:
        graph = luma_neutral_chroma_visible_scanline_filter_graph(
            profile_id=HOUSE_CRT_PROFILE_ID,
            strength=HOUSE_CRT_INTENSITY,
            width=1080,
            height=1920,
            fps=30.0,
            scanline_delta_y=8.0,
        )

        self.assertIn(",-8.000", graph)
        self.assertIn(",8.000", graph)
        self.assertIn("cb='cb(X,Y)':cr='cr(X,Y)'", graph)

    def test_visible_scanline_graph_supports_wider_high_visibility_bars(self) -> None:
        graph = luma_neutral_chroma_visible_scanline_filter_graph(
            profile_id=HOUSE_CRT_PROFILE_ID,
            strength=HOUSE_CRT_INTENSITY,
            width=1080,
            height=1920,
            fps=30.0,
            scanline_delta_y=16.0,
            scanline_period_pixels=8,
            scanline_band_pixels=2,
        )

        self.assertIn("between(mod(Y,8),0,1)", graph)
        self.assertIn("between(mod(Y,8),4,5)", graph)
        self.assertIn(",-16.000", graph)
        self.assertIn(",16.000", graph)
        self.assertIn("cb='cb(X,Y)':cr='cr(X,Y)'", graph)
        self.assertNotIn("color=c=black", graph)

    def test_scanline_strength_variants_record_exact_deltas(self) -> None:
        self.assertEqual(
            [
                (item["scanline_strength_variant_id"], item["scanline_delta_y"])
                for item in VISIBLE_SCANLINE_STRENGTH_VARIANTS
            ],
            [
                ("balanced_plus_y8", 8.0),
                ("strong_crt_y10", 10.0),
                ("max_safe_y12", 12.0),
            ],
        )

    def test_high_visibility_scanline_variants_record_exact_shape(self) -> None:
        self.assertEqual(
            [
                (
                    item["scanline_strength_variant_id"],
                    item["scanline_delta_y"],
                    item["scanline_period_pixels"],
                    item["scanline_band_pixels"],
                )
                for item in VISIBLE_SCANLINE_HIGH_VISIBILITY_VARIANTS
            ],
            [
                ("visible_bars_y16_p8", 16.0, 8, 2),
                ("assertive_bars_y20_p8", 20.0, 8, 2),
                ("max_visible_bars_y24_p8", 24.0, 8, 2),
            ],
        )

    def test_selected_scanline_variant_is_strongest_pass07c_choice(self) -> None:
        selected = selected_visible_scanline_variant()

        self.assertEqual(VISIBLE_SCANLINE_SELECTED_STRENGTH_VARIANT_ID, "max_visible_bars_y24_p8")
        self.assertEqual(selected["scanline_delta_y"], 24.0)
        self.assertEqual(selected["scanline_period_pixels"], 8)
        self.assertEqual(selected["scanline_band_pixels"], 2)

    def test_visible_scanline_full_pass_contract_records_selected_y24_fields(self) -> None:
        read = visible_scanline_contract_read()
        selected = read["selected_scanline_strength_variant"]

        self.assertEqual(VISIBLE_SCANLINE_FULL_PASS_ID, "house_crt_clean_source_lineage_visible_scanline_first8_pass_07")
        self.assertEqual(read["contract_status"], "selected_for_first8_pass07_review")
        self.assertEqual(selected["scanline_strength_variant_id"], "max_visible_bars_y24_p8")
        self.assertEqual(selected["scanline_delta_y"], 24.0)
        self.assertEqual(selected["scanline_period_pixels"], 8)
        self.assertEqual(selected["scanline_band_pixels"], 2)

    def test_scanline_metric_detects_visible_horizontal_structure(self) -> None:
        image = Image.new("RGB", (32, 32), (128, 128, 128))
        for y in range(32):
            row_value = 122 if y % 4 == 0 else 134 if y % 4 == 2 else 128
            for x in range(32):
                image.putpixel((x, y), (row_value, row_value, row_value))

        read = scanline_visibility_from_image(image)

        self.assertEqual(read["scanline_policy_id"], VISIBLE_SCANLINE_POLICY_ID)
        self.assertEqual(read["scanline_visibility_read"], "pass")
        self.assertGreater(read["signed_light_minus_dark_yavg"], 2.0)

    def test_scanline_metric_detects_high_visibility_wider_bar_structure(self) -> None:
        image = Image.new("RGB", (64, 64), (128, 128, 128))
        for y in range(64):
            cycle = y % 8
            row_value = 100 if cycle in {0, 1} else 156 if cycle in {4, 5} else 128
            for x in range(64):
                image.putpixel((x, y), (row_value, row_value, row_value))

        read = scanline_visibility_from_image(
            image,
            scanline_period_pixels=8,
            scanline_band_pixels=2,
            scanline_delta_y=28.0,
            scanline_strength_variant_id="fixture_visible_bars",
        )

        self.assertEqual(read["scanline_visibility_read"], "pass")
        self.assertEqual(read["scanline_period_pixels"], 8)
        self.assertEqual(read["scanline_band_pixels"], 2)
        self.assertGreater(read["signed_light_minus_dark_yavg"], 50.0)

    def test_ladder_metrics_increase_monotonically_from_pass07a(self) -> None:
        def metric(line_value: float, variant_id: str, delta_y: float) -> dict[str, object]:
            return {
                "texture_metrics": {"overall_read": "pass", "luma_yavg_delta": 0.0, "chroma_delta": 1.0},
                "scanline_metrics": {
                    "scanline_visibility_read": "pass",
                    "mean_signed_light_minus_dark_yavg": line_value,
                    "scanline_strength_variant_id": variant_id,
                    "scanline_delta_y": delta_y,
                },
            }

        sample = {
            "pass07a_texture_metrics": metric(12.0, "pass07a_y6_baseline", VISIBLE_SCANLINE_DELTA_RGB)["texture_metrics"],
            "pass07a_scanline_metrics": metric(12.0, "pass07a_y6_baseline", VISIBLE_SCANLINE_DELTA_RGB)["scanline_metrics"],
            "ladder_variants": {
                "balanced_plus_y8": metric(18.0, "balanced_plus_y8", 8.0),
                "strong_crt_y10": metric(23.0, "strong_crt_y10", 10.0),
                "max_safe_y12": metric(27.0, "max_safe_y12", 12.0),
            },
        }

        summary = summarize_scanline_strength_ladder([sample])
        self.assertEqual(summary["recommended_candidate"], "balanced_plus_y8")
        reads = summary["variant_reads"]
        self.assertLess(
            reads["balanced_plus_y8"]["mean_scanline_yavg"],
            reads["strong_crt_y10"]["mean_scanline_yavg"],
        )
        self.assertLess(
            reads["strong_crt_y10"]["mean_scanline_yavg"],
            reads["max_safe_y12"]["mean_scanline_yavg"],
        )

    def test_high_visibility_ladder_recommendation_uses_supplied_variants(self) -> None:
        def metric(line_value: float, variant_id: str, delta_y: float) -> dict[str, object]:
            return {
                "texture_metrics": {"overall_read": "pass", "luma_yavg_delta": 0.0, "chroma_delta": 1.0},
                "scanline_metrics": {
                    "scanline_visibility_read": "pass",
                    "mean_signed_light_minus_dark_yavg": line_value,
                    "scanline_strength_variant_id": variant_id,
                    "scanline_delta_y": delta_y,
                },
            }

        sample = {
            "pass07a_texture_metrics": metric(12.0, "pass07a_y6_baseline", VISIBLE_SCANLINE_DELTA_RGB)["texture_metrics"],
            "pass07a_scanline_metrics": metric(12.0, "pass07a_y6_baseline", VISIBLE_SCANLINE_DELTA_RGB)["scanline_metrics"],
            "ladder_variants": {
                "visible_bars_y16_p8": metric(37.0, "visible_bars_y16_p8", 16.0),
                "assertive_bars_y20_p8": metric(46.0, "assertive_bars_y20_p8", 20.0),
                "max_visible_bars_y24_p8": metric(55.0, "max_visible_bars_y24_p8", 24.0),
            },
        }

        summary = summarize_scanline_strength_ladder(
            [sample],
            variants=VISIBLE_SCANLINE_HIGH_VISIBILITY_VARIANTS,
            metrics_schema_version="fixture_schema",
        )

        self.assertEqual(summary["schema_version"], "fixture_schema")
        self.assertEqual(summary["recommended_candidate"], "visible_bars_y16_p8")
        self.assertIn("visible_bars_y16_p8", summary["variant_reads"])

    def test_source_lineage_rejects_pretextured_manifest_markers_and_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "pretextured_proof.json"
            manifest = {
                "historical_signal_texture_used": True,
                "historical_signal_texture_read": "pass",
                "texture_applied_path": "/tmp/historical_signal_texture/pass_01/clip.mp4",
                "visual_noaudio_path": "/tmp/historical_signal_texture/pass_01/clip.mp4",
            }
            reasons = source_manifest_pretextured_reasons(
                manifest,
                manifest_path,
                Path("/tmp/historical_signal_texture/pass_01/clip.mp4"),
            )

        self.assertTrue(source_path_is_pretextured("/tmp/historical_signal_texture/pass_01/clip.mp4"))
        self.assertIn("historical_signal_texture_used", {item["field"] for item in reasons})
        self.assertIn("historical_signal_texture_read", {item["field"] for item in reasons})
        self.assertIn("texture_applied_path", {item["field"] for item in reasons})
        self.assertIn("selected_visual_source_path", {item["field"] for item in reasons})

    def test_challenger_clean_source_plan_rejects_pass06_and_selects_pass11_contact_sheet(self) -> None:
        pass06_path = Path(
            "/Users/mike/Viz_CascadeEffects/references/episodes/challenger/shorts/challenger_short_scoped_v1/"
            "motion_video_proof/pass_06/challenger_short_scoped_v1_motion_video_proof_pass_06_audio_repair_20260425T104230Z__proof.json"
        )
        pass05_path = Path(
            "/Users/mike/Viz_CascadeEffects/references/episodes/challenger/shorts/challenger_short_scoped_v1/"
            "motion_video_proof/pass_05/manifest.json"
        )
        pass03_path = Path(
            "/Users/mike/Viz_CascadeEffects/references/episodes/challenger/shorts/challenger_short_scoped_v1/"
            "motion_video_proof/pass_03/manifest.json"
        )
        pass06_manifest = json.loads(pass06_path.read_text(encoding="utf-8"))

        self.assertTrue(source_manifest_pretextured_reasons(pass06_manifest, pass06_path))
        self.assertTrue(source_manifest_pretextured_reasons(json.loads(pass05_path.read_text(encoding="utf-8")), pass05_path))
        self.assertTrue(source_manifest_pretextured_reasons(json.loads(pass03_path.read_text(encoding="utf-8")), pass03_path))
        with mock.patch("house_crt_static_final_pass.duration", return_value=2.0):
            plan = resolve_clean_source_plan("challenger", pass06_path, pass06_manifest)

        self.assertTrue(plan.source_lineage_read["clean_source_confirmed"])
        self.assertEqual(plan.clean_source_proof_path.name, "manifest.json")
        self.assertIn("/motion_contact_sheet/pass_11/", str(plan.clean_source_proof_path))
        self.assertEqual(plan.source_lineage_read["selected_source_mode"], "ordered_clean_row_clip_sources")
        self.assertIn(str(pass06_path), plan.source_lineage_read["rejected_pretextured_source_paths"])

    def test_hyatt_clean_source_plan_rejects_pass12_and_selects_pass11_visual_noaudio(self) -> None:
        pass12_path = Path(
            "/Users/mike/Viz_CascadeEffects/references/episodes/hyatt-regency/shorts/hyatt_short_scoped_v1/"
            "motion_video_proof/pass_12_scene_led_challenger_matched_crt/"
            "hyatt_scene_led_motion_video_proof_pass_12_challenger_matched_crt__proof.json"
        )
        pass12_manifest = json.loads(pass12_path.read_text(encoding="utf-8"))

        self.assertTrue(source_manifest_pretextured_reasons(pass12_manifest, pass12_path))
        with mock.patch("house_crt_static_final_pass.duration", return_value=44.0):
            plan = resolve_clean_source_plan("hyatt", pass12_path, pass12_manifest)

        self.assertTrue(plan.source_lineage_read["clean_source_confirmed"])
        self.assertIn("/pass_11_scene_led_no_freeze_44s/", str(plan.clean_source_proof_path))
        self.assertIn("motion_proof_pass_11_visual_noaudio", str(plan.visual_source_path))
        self.assertEqual(plan.source_lineage_read["selected_source_mode"], "single_clean_no_caption_visual_source")
        self.assertIn(str(pass12_path), plan.source_lineage_read["rejected_pretextured_source_paths"])

    def test_luma_metric_gate_passes_and_fails_at_three_yavg(self) -> None:
        clean = {"yavg": 100.0, "chroma_magnitude": 10.0}
        pass_read = texture_metric_read(clean, {"yavg": 102.9, "chroma_magnitude": 11.0})
        fail_read = texture_metric_read(clean, {"yavg": 103.1, "chroma_magnitude": 11.0})

        self.assertEqual(pass_read["luma_neutral_read"], "pass")
        self.assertEqual(fail_read["luma_neutral_read"], "fail")
        self.assertEqual(LUMA_YAVG_TOLERANCE, 3.0)

    def test_color_sources_preserve_or_increase_chroma_and_monochrome_rejects_fake_color(self) -> None:
        color = texture_metric_read({"yavg": 100.0, "chroma_magnitude": 8.0}, {"yavg": 100.0, "chroma_magnitude": 9.5})
        monochrome = texture_metric_read({"yavg": 100.0, "chroma_magnitude": 0.4}, {"yavg": 100.0, "chroma_magnitude": 4.0})

        self.assertEqual(color["source_chroma_class"], "color")
        self.assertEqual(color["chroma_read"], "pass")
        self.assertEqual(monochrome["source_chroma_class"], "monochrome")
        self.assertEqual(monochrome["chroma_read"], "fail")

    def test_signal_interruption_constants_match_challenger_pass05_policy(self) -> None:
        self.assertEqual(SIGNAL_INTERRUPTION_PROFILE_ID, "era_1980s_horizontal_signal_interruption_v2_randomized")
        self.assertEqual(SIGNAL_INTERRUPTION_DURATION_SECONDS, 0.25)

    def test_signal_frame_mutation_retains_source_picture_structure(self) -> None:
        source = Image.new("RGB", (180, 120), (40, 80, 120))
        for x in range(180):
            for y in range(120):
                source.putpixel((x, y), ((x * 2) % 256, (y * 2) % 256, (x + y) % 256))
        config = {
            "variant_id": "thin_tracking_tears",
            "seed": 42,
            "order": 0,
            "band_count": 4,
            "band_heights": [3, 5, 7],
            "dx_range": (12, 30),
            "dropout_count": 2,
            "snow_strength": 0.18,
            "emphasis": "even",
            "line_alpha": 76,
            "chroma_shift": 8,
        }

        mutated = apply_signal_frame(source, config, frame_index=5, total_frames=8)
        diff = ImageChops.difference(source, mutated)

        self.assertIsNotNone(diff.getbbox())
        self.assertLess(sum(ImageChops.difference(source.convert("L"), mutated.convert("L")).histogram()[128:]), 180 * 120)


if __name__ == "__main__":
    unittest.main()
